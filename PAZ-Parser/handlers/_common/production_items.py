"""The items a worker production key produces, read from the `PRODUCTION_ITEMS` index.

    production_key -> plantexchangegroup.bss item_subgroup_key
                   -> itemsubgroup.dbss item keys

Shared by the tables that show production items (`plantexchangegroup.bss`,
`plantzone.dbss`). The index is built by `build_production_item_index` in
`_bss/plantexchangegroup/parser.py`.
"""

from __future__ import annotations

from _common.item_key import item_key_text
from _common.lookup_index import IndexKind, lookup


def production_item_keys(production_key: int) -> tuple[int, ...] | None:
    """The packed item keys a production key produces, or None when unknown."""
    value = lookup(IndexKind.PRODUCTION_ITEMS, production_key)
    return value if isinstance(value, tuple) else None


def production_item_fields(production_key: int) -> dict:
    """`item_keys` and item names for a record; `item_keys` is None when unknown."""
    item_keys = production_item_keys(production_key)
    if item_keys is None:
        return {"item_keys": None, "items": []}
    return {
        "item_keys": list(item_keys),
        "items": [item_key_text(key) for key in item_keys],
    }
