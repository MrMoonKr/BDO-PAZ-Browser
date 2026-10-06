from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import handler_text, load_handler_strings
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, size_column
from .parser import (
    parse_fairyskillchange_records,
    parse_fairyskillchangeoffset_records,
)


_LANG_DIR = Path(__file__).parent / "lang"


class FairySkillChangeHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR)["columns"]
        return [
            Column(cols["level"], "num", sort_key="level"),
            Column(cols["orbCost"], "num", sort_key="orb_cost"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return parse_fairyskillchange_records(data)

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]

        rows = [[e(record["level"]), e(record["orb_cost"])] for record in slice_]

        return table(handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records)), self._columns(), rows)


def fairy_skill_change_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("level", "level"),
            offset_column("data_offset", "dataOffset"),
            size_column("data_size", "dataSize"),
            offset_column("record_start", "recordStart"),
        ],
        parse_fairyskillchangeoffset_records,
    )
