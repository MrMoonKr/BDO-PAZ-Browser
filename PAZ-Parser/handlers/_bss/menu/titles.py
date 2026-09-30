"""English titles of the main menu categories and entries.

Both `menu.bss` and `submenu.bss` store a title as a UI string key with its
sheet; `stringtable.bss` gives the key's hash and LOC type 37 the text.
"""

from __future__ import annotations

from collections.abc import Iterable

from _bss.stringtable.text import KeyHashes, ui_key_hashes, ui_key_text

STRINGTABLE_FILE = "stringtable.bss"


def title_hashes(stringtable: bytes | None, records: Iterable[dict]) -> dict[str, dict[str, int]]:
    """Key hashes of every sheet the records' titles use."""
    return ui_key_hashes(stringtable, {record["sheet"] for record in records})


def menu_title(record: dict, hashes: KeyHashes) -> str:
    """The English title of a menu record, else its UI string key."""
    return ui_key_text(hashes, record["sheet"], record["title_key"]) or record["title_key"]
