from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, icon_cell, sort_keys, table
from _common.lang import handler_text, load_handler_strings
from _common.item_key import item_level_name
from .parser import parse_specialenchantitem_records


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"

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
    return item_level_name(record["item_id"], record["enchant_level"]) or record["name_kr"]


def _level_record(record: dict) -> dict:
    shown_as = display_level_text(record["display_level"])
    return {
        **record,
        # Shown As sorts by display_level. A level with no text (0) renders a
        # dash, so None makes it sort last.
        "display_level": record["display_level"] if shown_as else None,
        "shown_as": shown_as,
        "name": _level_name(record),
    }


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

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return [_level_record(record) for record in parse_specialenchantitem_records(data)]

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
                e(r["item_id"]),
                e(r["enchant_level"]),
                e(r["shown_as"] or _EMPTY),
                icon_cell(r["icon_path"]) if r["icon_path"] else _EMPTY,
                e(r["name"] or _EMPTY),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
