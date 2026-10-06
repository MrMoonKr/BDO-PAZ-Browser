"""`specialenchantitem.bss`: the items whose name or icon changes per level.

    PABR | u32 count | count x 19-byte row | string table | u32 string_table_start | u32 0

Each row holds a packed item key, the level the client shows, and string-table
indices for the icon path and the Korean name of that level. It copies the
per-level icons of `itemenchant.dbss` for these items. Full layout in
docs/file-formats/specialenchantitem_bss.md.
"""

from __future__ import annotations

import struct

from _common.binary import u32
from _common.item_key import split_item_key
from _common.pabr_strings import fixed_row_offsets, read_string_table, string_at, string_table_start


# Stored icon paths are relative to this folder, as in itemenchant.dbss.
ICON_ROOT = "ui_texture/icon/"

# u32 item_key | u8 display_level | u32 icon_ref | u32 name_ref | 4x
# | u8 unknown_11 | u8 unknown_12
_ROW = struct.Struct("<IBII4xBB")
_ROW_SIZE = 19
assert _ROW.size == _ROW_SIZE


def _row_offsets(data: bytes) -> range:
    """Start of every row. Raises ValueError when the rows do not fill the file."""
    return fixed_row_offsets(data, _ROW_SIZE, "specialenchantitem.bss")


def _icon_path(stored: str) -> str:
    return f"{ICON_ROOT}{stored.lower()}" if stored else ""


def parse_specialenchantitem_records(data: bytes) -> list[dict]:
    """Every item level row in file order, with its strings resolved.

    Raises ValueError on a bad magic, or when the rows do not end where the
    string table starts: then the row size has changed and every field is suspect.
    """
    offsets = _row_offsets(data)
    strings = read_string_table(data)
    records: list[dict] = []
    for offset in offsets:
        item_key, display_level, icon_ref, name_ref, unknown_11, unknown_12 = (
            _ROW.unpack_from(data, offset)
        )
        item_id, enchant_level = split_item_key(item_key)
        records.append({
            "item_key": item_key,
            "item_id": item_id,
            "enchant_level": enchant_level,
            "display_level": display_level,
            "icon_path": _icon_path(string_at(strings, icon_ref)),
            "name_kr": string_at(strings, name_ref),
            "unknown_11": unknown_11,
            "unknown_12": unknown_12,
        })
    return records


def build_item_key_icon_index(data: bytes) -> dict[int, str]:
    """Icon path by packed item key, for `IndexKind.ITEM_KEY_ICON`."""
    return {
        record["item_key"]: record["icon_path"]
        for record in parse_specialenchantitem_records(data)
        if record["icon_path"]
    }
