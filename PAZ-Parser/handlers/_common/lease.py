"""Lease options: items an NPC hands out for contribution points.

The `CHARACTER_LEASES` index maps a character to every lease option in its
dialogs as flat `(item_id, cost, ...)` pairs. It is built by
`build_character_lease_index` in `_dbss/detail_dialog/parser.py`, which also
reads the `buyItemByPoint(...)` action format (`_dbss/detail_dialog/lease.py`).
"""

from __future__ import annotations

from dataclasses import dataclass

from _common.item_key import item_name_tagged
from _common.lookup_index import IndexKind, lookup


@dataclass(frozen=True)
class Lease:
    item_id: int
    cost: int


def lease_pairs(value: tuple[int, ...]) -> list[Lease]:
    """Unpack a `CHARACTER_LEASES` value into leases."""
    return [Lease(item_id, cost) for item_id, cost in zip(value[::2], value[1::2])]


def dialog_leases(character_id: int) -> list[Lease]:
    """Every lease option in the character's dialogs, in dialog order; [] when unknown."""
    value = lookup(IndexKind.CHARACTER_LEASES, character_id)
    return lease_pairs(value) if isinstance(value, tuple) else []


def lease_text_tagged(lease: Lease, has_loc: bool) -> str:
    """`[CP] Small Fence (3 CP)`, the name in its item grade colour tag; the
    item ID stands in for a missing name."""
    name = (item_name_tagged(lease.item_id) if has_loc else "") or str(lease.item_id)
    return f"{name} ({lease.cost} CP)"
