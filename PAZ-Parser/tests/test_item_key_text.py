"""`item_key_text()`: an item level's own LOC type 79 name, else the item name and level."""
from __future__ import annotations

from collections.abc import Iterator

import pytest

import _common.loc as loc
from _common.item_key import item_key_text, item_level_name
from tests.loc_counter import reset_loc
from tests.loc_data import LocRow, loc_bytes

_SOVEREIGN = 715001
_PREONNE = 705536
_PLAIN = 11015

_ROWS: list[LocRow] = [
    (0, _SOVEREIGN, 0, 0, 0, "Sovereign Longsword"),
    (79, _SOVEREIGN, 0, 0, 0, "Sovereign Longsword"),
    (79, _SOVEREIGN, 10, 0, 0, "DEC: Sovereign Longsword"),
    # A level whose LOC type 79 name is only the item name tells no level apart.
    (0, _PREONNE, 0, 0, 0, "Preonne Belt"),
    (79, _PREONNE, 3, 0, 0, "Preonne Belt"),
    (0, _PLAIN, 0, 0, 0, "Blackstar Helmet"),
]


def _key(item_id: int, enchant_level: int) -> int:
    return enchant_level << 24 | item_id


@pytest.fixture(autouse=True)
def _loc() -> Iterator[None]:
    reset_loc()
    loc.init_loc(loc_bytes(_ROWS))
    yield
    reset_loc()


def test_level_with_its_own_name_shows_it_alone() -> None:
    assert item_key_text(_key(_SOVEREIGN, 10)) == "DEC: Sovereign Longsword"


def test_level_named_like_the_item_keeps_the_level() -> None:
    assert item_key_text(_key(_PREONNE, 3)) == "Preonne Belt (3)"


def test_level_without_a_level_name_keeps_the_level() -> None:
    assert item_key_text(_key(_PLAIN, 19)) == "Blackstar Helmet (19)"
    assert item_key_text(_key(_SOVEREIGN, 4)) == "Sovereign Longsword (4)"


def test_base_item_shows_the_item_name() -> None:
    assert item_key_text(_key(_SOVEREIGN, 0)) == "Sovereign Longsword"


def test_item_level_name_is_empty_on_a_miss() -> None:
    assert item_level_name(_PLAIN, 19) == ""
    reset_loc()
    assert item_level_name(_SOVEREIGN, 10) == ""
