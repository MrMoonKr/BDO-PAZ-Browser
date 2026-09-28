"""Every lease an NPC offers, from the dialog index and this file's own lease.

Kept out of `handler.py` so tests can import it without loading the handler
registry.
"""

from __future__ import annotations

from _common.lookup_index import IndexKind, lookup
from _dbss.detail_dialog.lease import Lease
from _dbss.detail_dialog.parser import lease_pairs


def character_leases(character_id: int, stored_item: int, stored_cost: int) -> list[Lease]:
    """Every lease of the character: the dialog leases, with the one stored here.

    The dialog leases come from the `CHARACTER_LEASES` index. Where the dialog
    and this file disagree on the cost, the game charges the cost stored here
    (Merio 43501, checked in game), so it replaces the dialog's. Without the
    index only the stored lease is known.
    """
    value = lookup(IndexKind.CHARACTER_LEASES, character_id)
    leases = lease_pairs(value) if isinstance(value, tuple) else []
    if not stored_item:
        return leases

    stored = Lease(stored_item, stored_cost)
    if all(lease.item_id != stored_item for lease in leases):
        return [stored, *leases]
    return [stored if lease.item_id == stored_item else lease for lease in leases]
