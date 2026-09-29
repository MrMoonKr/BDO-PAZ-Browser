"""The items a worker production key produces, as a lookup index.

    production_key -> plantexchangegroup.bss item_subgroup_key
                   -> itemsubgroup.dbss item keys

Only a few hundred of the 16,000+ subgroups are production subgroups, so the
`PRODUCTION_ITEMS` index holds just those instead of every table that shows
production items opening the 13 MB `itemsubgroup.dbss`.
"""

from __future__ import annotations

from _common.lookup_index import IndexKind, lookup
from _dbss.itemsubgroup.parser import subgroups_by_key
from .parser import parse_plantexchangegroup_records


def build_production_item_index(
    groups: bytes,
    subgroups: bytes,
    subgroup_offsets: bytes,
) -> dict[int, tuple[int, ...]]:
    """Map each production key to the packed item keys of its subgroup.

    Keys whose subgroup is missing from `itemsubgroupoffset.dbss` are left out.
    """
    rows = parse_plantexchangegroup_records(groups)
    found = subgroups_by_key(subgroups, subgroup_offsets, {row["item_subgroup_key"] for row in rows})
    return {
        row["production_key"]: found[row["item_subgroup_key"]].item_keys
        for row in rows
        if row["item_subgroup_key"] in found
    }


def production_item_keys(production_key: int) -> tuple[int, ...] | None:
    """The packed item keys a production key produces, or None when unknown."""
    value = lookup(IndexKind.PRODUCTION_ITEMS, production_key)
    return value if isinstance(value, tuple) else None
