from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, sprite_icon_cell, table
from _common.lang import load_handler_strings
from _bss.menu.parser import parse_menu_records
from _bss.menu.titles import STRINGTABLE_FILE, menu_title, title_hashes
from .parser import parse_submenu_records


_LANG_DIR = Path(__file__).parent / "lang"
_MENU_FILE = "menu.bss"
_EMPTY = "-"


class SubmenuBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("entryId", "Entry ID"), "num", sort_key="entry_id"),
            Column(cols.get("category", "Category"), sort_key="category"),
            Column(cols.get("position", "Position"), "num", sort_key="position"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("title", "Title"), sort_key="title"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/{_MENU_FILE}", f"{folder}/{STRINGTABLE_FILE}"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records = parse_submenu_records(data)
        menu_data = companions.get(_MENU_FILE)
        menus = parse_menu_records(menu_data) if menu_data is not None else []
        # Without stringtable.bss or LOC a title falls back to its key, and
        # without menu.bss the category to its ID.
        hashes = title_hashes(companions.get(STRINGTABLE_FILE), [*records, *menus])
        categories = {m["menu_id"]: menu_title(m, hashes) for m in menus}
        return [
            {
                **record,
                "category": categories.get(record["menu_id"], str(record["menu_id"])),
                "title": menu_title(record, hashes),
            }
            for record in records
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} menu entries"
        rows = [
            [
                e(r["entry_id"]),
                e(r["category"] or _EMPTY),
                e(r["position"]),
                sprite_icon_cell(r["icon_path"], r["icon_region"]),
                e(r["title"] or _EMPTY),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
