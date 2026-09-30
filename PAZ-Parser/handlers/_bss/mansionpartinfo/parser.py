"""`mansionpartinfo.bss`: the part blueprints of the manors in installation mode.

    PABR | u32 count | count x 12-byte row | string table | u32 string_table_start | u32 0

Each row names the house character of a manor, a part index and a
string-table index for the part icon. Full layout in
docs/file-formats/mansionpartinfo_bss.md.
"""

from __future__ import annotations

import struct

from _common.binary import u32
from _common.pabr_strings import TRAILER_SIZE, read_string_table, string_at, string_table_start


_MAGIC = b"PABR"
_HEADER_SIZE = 8

# Stored icon paths start at "Icon/", which hangs off ui_texture.
ICON_ROOT = "ui_texture/"

# u16 character_id | u8 unknown_02 | u8 part_index | u32 icon_ref | u32 unknown_str_ref
_ROW = struct.Struct("<HBBII")
_ROW_SIZE = 12
assert _ROW.size == _ROW_SIZE


def _row_offsets(data: bytes) -> range:
    """Start of every row. Raises ValueError when the rows do not fill the file."""
    if len(data) < _HEADER_SIZE + TRAILER_SIZE or data[:4] != _MAGIC:
        raise ValueError("mansionpartinfo.bss has invalid magic.")

    rows_end = _HEADER_SIZE + u32(data, 4) * _ROW_SIZE
    if rows_end != string_table_start(data):
        raise ValueError(
            f"mansionpartinfo.bss rows end at 0x{rows_end:X} but its string "
            f"table starts at 0x{string_table_start(data):X}"
        )
    return range(_HEADER_SIZE, rows_end, _ROW_SIZE)


def parse_mansionpartinfo_records(data: bytes) -> list[dict]:
    """Every manor part row in file order, with its strings resolved.

    Raises ValueError on a bad magic, or when the rows do not end where the
    string table starts: then the row size has changed and every field is suspect.
    """
    offsets = _row_offsets(data)
    strings = read_string_table(data)
    records: list[dict] = []
    for offset in offsets:
        character_id, unknown_02, part_index, icon_ref, unknown_str_ref = _ROW.unpack_from(data, offset)
        icon = string_at(strings, icon_ref)
        records.append({
            "character_id": character_id,
            "part_index": part_index,
            "icon_path": f"{ICON_ROOT}{icon.lower()}" if icon else "",
            "unknown_02": unknown_02,
            "unknown_str": string_at(strings, unknown_str_ref),
        })
    return records


def manor_part_key(character_id: int, part_index: int) -> int:
    """`IndexKind.MANOR_PART_ICON` key: the part above the u16 manor character."""
    return part_index << 16 | character_id


def build_manor_part_icon_index(data: bytes) -> dict[int, str]:
    """Part icon path by `manor_part_key()`, for `IndexKind.MANOR_PART_ICON`."""
    return {
        manor_part_key(record["character_id"], record["part_index"]): record["icon_path"]
        for record in parse_mansionpartinfo_records(data)
        if record["icon_path"]
    }
