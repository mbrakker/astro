from dataclasses import asdict

import pytest

from pathlib import Path

from xml.etree import ElementTree

from tarot import (
    TarotDrawRequest,
    TarotImageRequest,
    draw_spread,
    load_card,
    load_cards,
    resolve_card_image,
)


def test_database_contains_complete_deck() -> None:
    cards = load_cards()
    assert len(cards) == 78
    assert len({card.id for card in cards}) == 78


def test_draw_is_reproducible_and_round_trips() -> None:
    request = TarotDrawRequest(spread_type="three", seed="2026-08-01")
    first = draw_spread(request)
    second = draw_spread(TarotDrawRequest(**asdict(request)))
    assert first == second
    assert [card.position for card in first.cards] == ["Прошлое", "Настоящее", "Будущее"]


def test_load_card_rejects_unknown_id() -> None:
    with pytest.raises(KeyError):
        load_card("not-a-card")


def test_request_validation_rejects_unknown_spread() -> None:
    with pytest.raises(ValueError):
        draw_spread(TarotDrawRequest(spread_type="celtic-cross"))


def test_every_card_has_upright_and_reversed_image() -> None:
    for card in load_cards():
        upright = resolve_card_image(TarotImageRequest(card=card))
        reversed_image = resolve_card_image(TarotImageRequest(card=card, reversed=True))
        assert (upright.width, upright.height) == (360, 600)
        assert (reversed_image.width, reversed_image.height) == (360, 600)


def test_spread_table_backgrounds_are_valid_images() -> None:
    table_paths = sorted((Path(__file__).parents[1] / "assets" / "tables").glob("scarlet_table*.svg"))
    assert len(table_paths) == 3
    for table_path in table_paths:
        root = ElementTree.parse(table_path).getroot()
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert (root.attrib["width"], root.attrib["height"]) == ("1200", "800")
