"""`loc_type_entries()`: one LOC type's keys and texts, following the loaded index."""
from __future__ import annotations

from collections.abc import Iterator

import pytest

import _common.loc as loc
from tests.loc_counter import reset_loc
from tests.loc_data import LocRow, loc_bytes

_ROWS: list[LocRow] = [
    (50, 114415, 0, 12, 0, "Gloves"),
    (50, 114415, 0, 12, 3, "<PAColor0xffe9bd23>Contains<PAOldColor>"),
    (6, 300, 0, 0, 0, "gamma"),
]


@pytest.fixture(autouse=True)
def _clear_loc() -> Iterator[None]:
    reset_loc()
    yield
    reset_loc()


def test_returns_only_the_rows_of_one_type() -> None:
    loc.init_loc(loc_bytes(_ROWS))

    assert dict(loc.loc_type_entries(50)) == {
        (50, 114415, 0, 12, 0): "Gloves",
        (50, 114415, 0, 12, 3): "<PAColor0xffe9bd23>Contains<PAOldColor>",
    }


def test_is_empty_without_loc() -> None:
    assert not loc.loc_type_entries(50)


def test_is_read_only() -> None:
    loc.init_loc(loc_bytes(_ROWS))

    with pytest.raises(TypeError):
        loc.loc_type_entries(50)[(50, 1, 0, 12, 0)] = "x"  # type: ignore[index]


def test_follows_a_swapped_index() -> None:
    """The test runner swaps `_LOC_INDEX` in place of `init_loc()`."""
    loc.init_loc(loc_bytes([(6, 400, 0, 0, 0, "delta")]))
    swapped = loc._LOC_INDEX
    loc.init_loc(loc_bytes(_ROWS))
    assert dict(loc.loc_type_entries(6)) == {(6, 300, 0, 0, 0): "gamma"}

    loc._LOC_INDEX = swapped

    assert dict(loc.loc_type_entries(6)) == {(6, 400, 0, 0, 0): "delta"}
