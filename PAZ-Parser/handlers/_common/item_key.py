"""Packed item keys and item names shared by the item tables.

`itemenchant.dbss`, `itemsubgroup.dbss` and the tables that hand out items
pack an item and its enhancement level into one key:

    item_key = enchant_level << 24 | item_id

Level 0 is the base item. LOC type 0 names an item by its ID alone, so every
level of one item shares a name. See docs/file-formats/itemenchant_dbss.md.
"""

from __future__ import annotations

from _common.loc import loc_text

LOC_ITEM_NAME = 0

_ITEM_ID_MASK = 0x00FFFFFF
_ENCHANT_LEVEL_SHIFT = 24


def split_item_key(item_key: int) -> tuple[int, int]:
    """`(item_id, enchant_level)` of an item key."""
    return item_key & _ITEM_ID_MASK, item_key >> _ENCHANT_LEVEL_SHIFT


def item_name(item_id: int) -> str:
    """LOC type 0 name of an item, or '' when it has none or LOC is not loaded."""
    return loc_text(LOC_ITEM_NAME, item_id)


def item_key_text(item_key: int) -> str:
    """`Blackstar Helmet (19)`: the item name, then the level when above 0.

    The item ID stands in for a missing name.
    """
    item_id, enchant_level = split_item_key(item_key)
    name = item_name(item_id) or str(item_id)
    return f"{name} ({enchant_level})" if enchant_level else name
