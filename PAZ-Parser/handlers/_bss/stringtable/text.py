"""LOC text of a UI string key, for tables that store keys instead of text.

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
# LOC str_id3 of a key's text, in lookup order: some keys only have variant 1.
_LOC_VARIANTS = (0, 1)

# sheet -> {key -> key_hash}
KeyHashes = Mapping[str, Mapping[str, int]]


def ui_key_hashes(stringtable: bytes | None, sheets: Iterable[str]) -> dict[str, dict[str, int]]:
    """The key hashes of the named sheets, or none without `stringtable.bss`."""
    if stringtable is None:
        return {}
    return parse_sheet_key_hashes(stringtable, [s for s in sheets if s in SHEET_LOC_ID2])


def ui_hash_tagged(sheet: str, key_hash: int) -> str:
    """LOC type 37 text of a key hash in a sheet with its PA tags, or '' when the
    sheet or text is missing.

    Tries LOC `str_id3` 0 first, then the variant 1 that some keys only have.
    """
    loc_id2 = SHEET_LOC_ID2.get(sheet)
    if loc_id2 is None:
        return ""
    for variant in _LOC_VARIANTS:
        text = loc_lookup(LOC_UI_STRING, key_hash, loc_id2, variant)
        if text:
            return text.strip()
    return ""


def ui_hash_text(sheet: str, key_hash: int) -> str:
    """`ui_hash_tagged` without its PA tags."""
    return strip_pa_tags(ui_hash_tagged(sheet, key_hash)).strip()


def ui_key_text(hashes: KeyHashes, sheet: str, key: str) -> str:
    """LOC type 37 text of a UI string key, or '' when the sheet, hash or text is missing."""
    key_hash = hashes.get(sheet, {}).get(key)
    return "" if key_hash is None else ui_hash_text(sheet, key_hash)
