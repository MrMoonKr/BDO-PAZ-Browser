"""Server-side sort order for parsed tables.

Parsed tables are paged, so sorting has to happen over the full record list
before a page is sliced. Sorting uses the raw record values a handler declares
(``duration_ms``, not the rendered ``1h 30m``), so hex offsets, durations and
dash cells order correctly.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast

SORT_ASC = "asc"
SORT_DESC = "desc"
SORT_DIRECTIONS = frozenset({SORT_ASC, SORT_DESC})

# Type ranks keep mixed columns ordered: numbers first, then text, then
# anything else (lists, tuples) by its string form.
_RANK_NUMBER = 0
_RANK_TEXT = 1
_RANK_OTHER = 2


@dataclass(frozen=True)
class TableSort:
    """Active sort of a parsed table: a record field and a direction."""

    field: str
    direction: str

    @property
    def descending(self) -> bool:
        return self.direction == SORT_DESC

    def to_dict(self) -> dict[str, str]:
        return {"field": self.field, "dir": self.direction}

    @classmethod
    def parse(cls, field: object, direction: object) -> TableSort | None:
        """Build a sort from untrusted input, or None when it is malformed."""
        if not isinstance(field, str) or not field:
            return None
        if direction not in SORT_DIRECTIONS:
            return None
        return cls(field, str(direction))


def _sort_key(value: object) -> tuple[int, object] | None:
    """Comparable key for a raw record value, or None for an empty value."""
    if value is None:
        return None
    if isinstance(value, bool):
        return (_RANK_NUMBER, int(value))
    if isinstance(value, (int, float)):
        if value != value:  # NaN never compares, so treat it as empty
            return None
        return (_RANK_NUMBER, value)
    if isinstance(value, str):
        text = value.strip()
        return (_RANK_TEXT, text.casefold()) if text else None
    if isinstance(value, (list, tuple, set, frozenset, dict)) and not value:
        return None
    return (_RANK_OTHER, str(value).casefold())


def sort_order(records: list[dict], field: str, descending: bool) -> list[int]:
    """Record indices in sorted order. See `sort_order_by_values`."""
    return sort_order_by_values([record.get(field) for record in records], descending)


def sort_order_by_values(values: Sequence[object], descending: bool) -> list[int]:
    """Indices of `values` in sorted order.

    Empty values (None, blank strings, empty lists, NaN) go last in both
    directions. The sort is stable, so equal values keep their file order.
    """
    # Most sortable columns are plain integer IDs. Sorting those directly
    # skips building a key tuple per row, which matters at a million rows.
    if all(type(value) is int for value in values):
        return sorted(range(len(values)), key=values.__getitem__, reverse=descending)
    if all(type(value) is str for value in values):
        return _sort_order_text(cast("Sequence[str]", values), descending)

    keyed: list[tuple[tuple[int, object], int]] = []
    empty: list[int] = []

    for index, value in enumerate(values):
        key = _sort_key(value)
        if key is None:
            empty.append(index)
        else:
            keyed.append((key, index))

    keyed.sort(key=lambda item: item[0], reverse=descending)
    return [index for _, index in keyed] + empty


def _sort_order_text(values: Sequence[str], descending: bool) -> list[int]:
    """`sort_order_by_values` for an all-text column, without per-row key tuples."""
    keys = [value.strip().casefold() for value in values]
    filled = [index for index, key in enumerate(keys) if key]
    empty = [index for index, key in enumerate(keys) if not key]
    filled.sort(key=keys.__getitem__, reverse=descending)
    return filled + empty


def positions_in_order(order: Sequence[int], indices: list[int]) -> list[int]:
    """Map file-order record indices to their positions in a sorted view."""
    position = [0] * len(order)
    for pos, index in enumerate(order):
        position[index] = pos
    return sorted(position[index] for index in indices)
