"""`groupcameradata.bss`: the summaries shown when a story cutscene is skipped.

    PABR | u32 count | count x 28-byte row | string table | u32 string_table_start | u32 0

Each row holds a scene ID and string-table indices for the Korean title,
recap and quote and the region symbol icon. Full layout in
docs/file-formats/groupcameradata_bss.md.
"""

from __future__ import annotations

import struct

from _common.binary import u32
from _common.pabr_strings import TRAILER_SIZE, read_string_table, string_at, string_table_start


_MAGIC = b"PABR"
_HEADER_SIZE = 8

# Stored icon paths start at "Combine/", which hangs off ui_texture.
ICON_ROOT = "ui_texture/"

# u32 scene_id | u32 title_ref | u32 description_ref | u32 quote_ref | u32 icon_ref | 8x
_ROW = struct.Struct("<5I8x")
_ROW_SIZE = 28
assert _ROW.size == _ROW_SIZE


def _row_offsets(data: bytes) -> range:
    """Start of every row. Raises ValueError when the rows do not fill the file."""
    if len(data) < _HEADER_SIZE + TRAILER_SIZE or data[:4] != _MAGIC:
        raise ValueError("groupcameradata.bss has invalid magic.")

    rows_end = _HEADER_SIZE + u32(data, 4) * _ROW_SIZE
    if rows_end != string_table_start(data):
        raise ValueError(
            f"groupcameradata.bss rows end at 0x{rows_end:X} but its string "
            f"table starts at 0x{string_table_start(data):X}"
        )
    return range(_HEADER_SIZE, rows_end, _ROW_SIZE)


def parse_groupcameradata_records(data: bytes) -> list[dict]:
    """Every cutscene row in file order, with its strings resolved.

    Raises ValueError on a bad magic, or when the rows do not end where the
    string table starts: then the row size has changed and every field is suspect.
    """
    offsets = _row_offsets(data)
    strings = read_string_table(data)
    records: list[dict] = []
    for offset in offsets:
        scene_id, title_ref, description_ref, quote_ref, icon_ref = _ROW.unpack_from(data, offset)
        icon = string_at(strings, icon_ref)
        records.append({
            "scene_id": scene_id,
            "icon_path": f"{ICON_ROOT}{icon.lower()}" if icon else "",
            "title_kr": string_at(strings, title_ref),
            "description_kr": string_at(strings, description_ref),
            "quote_kr": string_at(strings, quote_ref),
        })
    return records


def build_cutscene_icon_index(data: bytes) -> dict[int, str]:
    """Region symbol path by scene ID, for `IndexKind.CUTSCENE_ICON`."""
    return {
        record["scene_id"]: record["icon_path"]
        for record in parse_groupcameradata_records(data)
        if record["icon_path"]
    }
