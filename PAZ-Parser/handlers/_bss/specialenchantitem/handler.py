from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, icon_cell, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import loc_lookup, strip_pa_tags
from .parser import parse_specialenchantitem_records


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"

# Keyed by item ID (str_id1) and enhancement level (str_id2).
_LOC_ITEM_LEVEL_NAME = 79

# Display levels above +15 are drawn as grades; LOC type 79 names confirm them.
_FIRST_GRADE_LEVEL = 16
_GRADES = ("PRI", "DUO", "TRI", "TET", "PEN", "HEX", "SEP", "OCT", "NOV", "DEC")


def display_level_text(display_level: int) -> str:
    """`+7`, `PEN` or `DEC` for a display level; '' for 0 or a value past DEC."""
    if display_level <= 0:
        return ""
    if display_level < _FIRST_GRADE_LEVEL:
        return f"+{display_level}"

    grade = display_level - _FIRST_GRADE_LEVEL
    return _GRADES[grade] if grade < len(_GRADES) else ""


def _level_name(record: dict) -> str:
    """LOC type 79 name of this item level, else the stored Korean name."""
    text = loc_lookup(_LOC_ITEM_LEVEL_NAME, record["item_id"], record["enchant_level"])
    return strip_pa_tags(text).strip() or record["name_kr"]


class SpecialEnchantItemBssHandler(PreviewHandler):
    def _strings(self) -> dict:
        return load_handler_strings(self.lang, _LANG_DIR)

    def _columns(self) -> list[Column]:
        cols = self._strings().get("columns", {})
        return [
            Column(cols.get("itemId", "Item ID"), "num", sort_key="item_id"),
            Column(cols.get("maxLevel", "Max Level"), "num", sort_key="enchant_level"),
            Column(cols.get("shownAs", "Shown As"), sort_key="display_level"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("name", "Name"), sort_key="name"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return [
            {
                **record,
                "shown_as": display_level_text(record["display_level"]),
                "name": _level_name(record),
            }
            for record in parse_specialenchantitem_records(data)
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} item levels"
        rows = [
            [
                e(r["item_id"]),
                e(r["enchant_level"]),
                e(r["shown_as"] or _EMPTY),
                icon_cell(r["icon_path"]) if r["icon_path"] else _EMPTY,
                e(r["name"] or _EMPTY),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
