"""Versioned contracts for tarot service inputs and outputs."""

from dataclasses import asdict, dataclass
from typing import Any

SCHEMA_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class TarotDrawRequest:
    """Request for a reproducible tarot spread.

    ``spread_type`` is either ``one`` or ``three``; ``seed`` controls selection
    and orientation, allowing a draw to be reproduced exactly.
    """

    spread_type: str = "one"
    seed: str | int | None = None
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> None:
        """Reject unsupported contract versions and spread types."""
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema version: {self.schema_version}")
        if self.spread_type not in {"one", "three"}:
            raise ValueError(f"Unsupported spread type: {self.spread_type}")


@dataclass(frozen=True, slots=True)
class TarotCard:
    """A card and its meaning as stored in the tarot database."""

    id: str
    name: str
    arcana: str
    suit: str | None
    number: int | None
    image_path: str | None
    upright_text: str | None
    reversed_text: str | None
    suit_archetype: str | None
    number_archetype: str | None
    reversed: bool = False
    position: str | None = None
    schema_version: str = SCHEMA_VERSION

    @property
    def interpretation(self) -> str | None:
        """Return the meaning matching the card orientation."""
        return self.reversed_text if self.reversed else self.upright_text

    def to_dict(self) -> dict[str, Any]:
        """Serialize the contract without losing optional fields."""
        return asdict(self)

    def validate(self) -> None:
        """Validate required database output fields."""
        if self.schema_version != SCHEMA_VERSION or not self.id or not self.name or not self.arcana:
            raise ValueError("Invalid tarot card contract")


@dataclass(frozen=True, slots=True)
class TarotSpread:
    """A validated ordered collection of drawn cards."""

    spread_type: str
    cards: tuple[TarotCard, ...]
    seed: str | int | None
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> None:
        """Ensure spread cardinality and every nested card are valid."""
        expected = {"one": 1, "three": 3}.get(self.spread_type)
        if self.schema_version != SCHEMA_VERSION or expected != len(self.cards):
            raise ValueError("Invalid tarot spread contract")
        for card in self.cards:
            card.validate()


@dataclass(frozen=True, slots=True)
class TarotImageRequest:
    """Request for the bundled image associated with ``card``.

    ``card`` is a validated card returned by the database service and
    ``reversed`` selects the physically rotated asset.
    """

    card: TarotCard
    reversed: bool = False
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> None:
        """Validate the request and its nested card contract."""
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema version: {self.schema_version}")
        self.card.validate()


@dataclass(frozen=True, slots=True)
class TarotImage:
    """Validated filesystem result for one bundled card image.

    ``path`` is absolute, ``media_type`` identifies its encoding, and
    ``width``/``height`` describe its pixel dimensions.
    """

    card_id: str
    path: str
    media_type: str
    width: int
    height: int
    reversed: bool
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> None:
        """Validate the image metadata returned by the filesystem service."""
        if (
            self.schema_version != SCHEMA_VERSION
            or not self.card_id
            or not self.path
            or self.media_type != "image/svg+xml"
            or self.width <= 0
            or self.height <= 0
        ):
            raise ValueError("Invalid tarot image contract")
