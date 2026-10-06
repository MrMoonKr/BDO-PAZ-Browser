from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, sprite_icon_cell, table
from _common.lang import handler_text, load_handler_strings
from .parser import parse_menu_records
from _bss.stringtable.text import STRINGTABLE_FILE
from .titles import menu_title, title_hashes


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"


class MenuBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("menuId", "Menu ID"), "num", sort_key="menu_id"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("title", "Title"), sort_key="title"),
            Column(cols.get("hotkey", "Hotkey"), sort_key="hotkey"),
            Column(cols.get("entries", "Entries"), "num", sort_key="submenu_count"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/{STRINGTABLE_FILE}"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        # Without stringtable.bss or LOC the title falls back to its key.
        records = parse_menu_records(data)
        hashes = title_hashes(companions.get(STRINGTABLE_FILE), records)
        return [{**record, "title": menu_title(record, hashes)} for record in records]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records))
        rows = [
            [
                e(r["menu_id"]),
                sprite_icon_cell(r["icon_path"], r["icon_region"]),
                e(r["title"] or _EMPTY),
                e(r["hotkey"] or _EMPTY),
                e(r["submenu_count"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
