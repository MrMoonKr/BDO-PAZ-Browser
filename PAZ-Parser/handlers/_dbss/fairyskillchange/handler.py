from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings
from .parser import (
    parse_fairyskillchange_records,
    parse_fairyskillchangeoffset_records,
)


_LANG_DIR = Path(__file__).parent / "lang"


class FairySkillChangeHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("level", "Level"), "num", sort_key="level"),
            Column(cols.get("orbCost", "Theiah's Orbs"), "num", sort_key="orb_cost"),
        ]

    def sortable_fields(self) -> frozenset[str]:
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

        return table(f"{len(records):,} fairy level records", self._columns(), rows)


class FairySkillChangeOffsetHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("offsetColumns", {})
        return [
            Column(cols.get("level", "Level"), "num", sort_key="level"),
            Column(cols.get("dataOffset", "Data Offset"), "num", sort_key="data_offset"),
            Column(cols.get("dataSize", "Data Size"), "num", sort_key="data_size"),
            Column(cols.get("recordStart", "Record Start"), "num", sort_key="record_start"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return parse_fairyskillchangeoffset_records(data)

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]

        rows = [
            [
                e(record["level"]),
                e(f"0x{record['data_offset']:08X}"),
                e(record["data_size"]),
                e(f"0x{record['record_start']:08X}"),
            ]
            for record in slice_
        ]

        return table(f"{len(records):,} fairy level offset records", self._columns(), rows)
