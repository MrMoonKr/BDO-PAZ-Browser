"""Lease options: dialog actions that hand out an item for contribution points.

A lease option's action is `buyItemByPoint(item, 0, 1, 5, cost)`: the item key,
two fixed values, a fixed `5` and the contribution point cost. Full notes in
docs/file-formats/detail_dialog_dbss.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from _common.item_key import item_name_tagged
from _common.pa_text import strip_pa_tags

_LEASE_ACTION = re.compile(r"buyItemByPoint\((\d+),\s*\d+,\s*\d+,\s*\d+,\s*(\d+)\)", re.IGNORECASE)


@dataclass(frozen=True)
class Lease:
    item_id: int
    cost: int


def parse_lease(action: str) -> Lease | None:
    """The leased item and its cost, or None when the action leases nothing."""
    match = _LEASE_ACTION.search(action)
    if match is None:
        return None
    return Lease(item_id=int(match.group(1)), cost=int(match.group(2)))


def lease_text_tagged(lease: Lease, has_loc: bool) -> str:
    """`[CP] Small Fence (3 CP)`, the name in its item grade colour tag; the
    item ID stands in for a missing name."""
    name = (item_name_tagged(lease.item_id) if has_loc else "") or str(lease.item_id)
    return f"{name} ({lease.cost} CP)"


def lease_text(lease: Lease, has_loc: bool) -> str:
    """`lease_text_tagged` as plain text."""
    return strip_pa_tags(lease_text_tagged(lease, has_loc)).strip()
