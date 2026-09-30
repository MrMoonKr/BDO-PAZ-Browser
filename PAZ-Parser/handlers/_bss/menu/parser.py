"""`menu.bss`: the main menu (Esc menu) categories.

    PABR | u32 count | count x 40-byte row | string table | u32 string_table_start | u32 0

Each row holds the category ID, its icon as a region of a sprite sheet, its
hotkey, its title as a UI string key with the key's sheet, and how many
`submenu.bss` entries it has. Full layout in docs/file-formats/menu_bss.md.
"""

from __future__ import annotations

import struct

from _common.binary import u32
from _common.pabr_strings import TRAILER_SIZE, read_string_table, string_at, string_table_start


_MAGIC = b"PABR"
_HEADER_SIZE = 8

# Stored sprite sheets start at "Combine/", which hangs off ui_texture.
ICON_ROOT = "ui_texture/"

# u32 menu_id | u32 x1 | u32 y1 | u32 x2 | u32 y2 | u32 icon_ref | u32 hotkey_ref
# | u32 sheet_ref | u32 key_ref | u32 submenu_count
_ROW = struct.Struct("<10I")
_ROW_SIZE = 40
assert _ROW.size == _ROW_SIZE


def sprite_sheet_path(stored: str) -> str:
    """PAZ path of a stored menu sprite sheet, or '' when there is none."""
    return f"{ICON_ROOT}{stored.lower()}" if stored else ""


def _row_offsets(data: bytes) -> range:
    """Start of every row. Raises ValueError when the rows do not fill the file."""
    if len(data) < _HEADER_SIZE + TRAILER_SIZE or data[:4] != _MAGIC:
        raise ValueError("menu.bss has invalid magic.")

    rows_end = _HEADER_SIZE + u32(data, 4) * _ROW_SIZE
    if rows_end != string_table_start(data):
        raise ValueError(
            f"menu.bss rows end at 0x{rows_end:X} but its string table "
            f"starts at 0x{string_table_start(data):X}"
        )
    return range(_HEADER_SIZE, rows_end, _ROW_SIZE)


def parse_menu_records(data: bytes) -> list[dict]:
    """Every category row in file order, with its strings resolved.

    Raises ValueError on a bad magic, or when the rows do not end where the
    string table starts: then the row size has changed and every field is suspect.
    """
    offsets = _row_offsets(data)
    strings = read_string_table(data)
    records: list[dict] = []
    for offset in offsets:
        (
            menu_id, x1, y1, x2, y2, icon_ref, hotkey_ref, sheet_ref, key_ref, submenu_count,
        ) = _ROW.unpack_from(data, offset)
        records.append({
            "menu_id": menu_id,
            "icon_path": sprite_sheet_path(string_at(strings, icon_ref)),
            "icon_region": (x1, y1, x2, y2),
            "hotkey": string_at(strings, hotkey_ref),
            "sheet": string_at(strings, sheet_ref),
            "title_key": string_at(strings, key_ref),
            "submenu_count": submenu_count,
        })
    return records


def build_menu_icon_index(data: bytes) -> dict[int, str]:
    """Sprite sheet path by menu ID, for `IndexKind.MENU_ICON`."""
    return {r["menu_id"]: r["icon_path"] for r in parse_menu_records(data) if r["icon_path"]}


def build_menu_icon_region_index(data: bytes) -> dict[int, tuple[int, ...]]:
    """Sprite region by menu ID, for `IndexKind.MENU_ICON_REGION`."""
    return {r["menu_id"]: r["icon_region"] for r in parse_menu_records(data) if r["icon_path"]}

