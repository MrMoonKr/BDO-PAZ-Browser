"""English text of a UI string key, for tables that store keys instead of text.

`menu.bss` and `submenu.bss` name their titles by sheet and key
(`GAME` / `LUA_MENU_REMAKE_CATEGORY_1`). The key's hash comes from
`stringtable.bss`, and LOC type 37 holds the text under that hash and the
sheet's `str_id2`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from _common.loc import loc_lookup, strip_pa_tags
from .parser import SHEET_LOC_ID2, parse_sheet_key_hashes

LOC_UI_STRING = 37

# sheet -> {key -> key_hash}
KeyHashes = Mapping[str, Mapping[str, int]]


def ui_key_hashes(stringtable: bytes | None, sheets: Iterable[str]) -> dict[str, dict[str, int]]:
    """The key hashes of the named sheets, or none without `stringtable.bss`."""
    if stringtable is None:
        return {}
    return parse_sheet_key_hashes(stringtable, [s for s in sheets if s in SHEET_LOC_ID2])


def ui_key_text(hashes: KeyHashes, sheet: str, key: str) -> str:
    """LOC type 37 text of a UI string key, or '' when the sheet, hash or text is missing."""
    loc_id2 = SHEET_LOC_ID2.get(sheet)
    key_hash = hashes.get(sheet, {}).get(key)
    if loc_id2 is None or key_hash is None:
        return ""
    return strip_pa_tags(loc_lookup(LOC_UI_STRING, key_hash, loc_id2)).strip()
