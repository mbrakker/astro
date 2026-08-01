"""The single SQLite service for tarot card persistence and draws."""

import json
import logging
import random
import sqlite3
from pathlib import Path

from tarot.contracts import TarotCard, TarotDrawRequest, TarotSpread

MODULE = __name__
ROLE = "service"
DEFAULT_DB_PATH = Path(__file__).parents[3] / "data" / "tarot.sql"
LOGGER = logging.getLogger(MODULE)


def _log(event: str, **context: object) -> None:
    """Emit a structured event without exposing card text or user data."""
    payload = {"event": event, "module": MODULE, "role": ROLE, **context}
    LOGGER.info(json.dumps(payload, ensure_ascii=False, default=str))


def _connect(db_path: Path) -> sqlite3.Connection:
    resolved = db_path.expanduser().resolve()
    _log("database_connect", run_id="local", task_id="tarot", span_id="sqlite", path=resolved)
    if not resolved.is_file():
        raise FileNotFoundError(f"Tarot database not found: {resolved}")
    sql = resolved.read_text(encoding="utf-8")
    connection = sqlite3.connect(":memory:")
    connection.executescript(sql)
    connection.row_factory = sqlite3.Row
    return connection


def _adapt(row: sqlite3.Row, *, reversed: bool = False, position: str | None = None) -> TarotCard:
    card = TarotCard(**dict(row), reversed=reversed, position=position)
    card.validate()
    return card


def load_cards(db_path: Path = DEFAULT_DB_PATH) -> tuple[TarotCard, ...]:
    """Load and validate all cards from the read-only SQLite database."""
    _log("load_cards_start", run_id="local", task_id="tarot", span_id="load-all")
    with _connect(db_path) as connection:
        rows = connection.execute("SELECT * FROM tarot_cards ORDER BY id").fetchall()
    cards = tuple(_adapt(row) for row in rows)
    if not cards:
        raise ValueError("Tarot database is empty")
    _log("load_cards_end", run_id="local", task_id="tarot", span_id="load-all", count=len(cards))
    return cards


def load_card(card_id: str, db_path: Path = DEFAULT_DB_PATH) -> TarotCard:
    """Load one card by its normalized identifier."""
    normalized_id = card_id.strip()
    if not normalized_id:
        raise ValueError("card_id must not be empty")
    with _connect(db_path) as connection:
        row = connection.execute("SELECT * FROM tarot_cards WHERE id = ?", (normalized_id,)).fetchone()
    if row is None:
        raise KeyError(f"Unknown tarot card: {normalized_id}")
    card = _adapt(row)
    _log("load_card_end", run_id="local", task_id="tarot", span_id="load-one", card_id=card.id)
    return card


def draw_spread(request: TarotDrawRequest, db_path: Path = DEFAULT_DB_PATH) -> TarotSpread:
    """Draw one card or a past/present/future spread without replacement."""
    request.validate()
    cards = load_cards(db_path)
    count = 1 if request.spread_type == "one" else 3
    positions = (None,) if count == 1 else ("Прошлое", "Настоящее", "Будущее")
    rng = random.Random(request.seed)
    selected = rng.sample(cards, count)
    drawn = tuple(
        TarotCard(
            **{key: value for key, value in card.to_dict().items() if key not in {"reversed", "position", "schema_version"}},
            reversed=bool(rng.getrandbits(1)),
            position=positions[index],
        )
        for index, card in enumerate(selected)
    )
    spread = TarotSpread(request.spread_type, drawn, request.seed)
    spread.validate()
    _log("draw_spread_end", run_id="local", task_id="tarot", span_id="draw", spread_type=request.spread_type, card_ids=[card.id for card in drawn])
    return spread
