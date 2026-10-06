from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import handler_text, load_handler_strings
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, size_column
from .parser import parse_petexp_records, parse_petexpoffset_records


_LANG_DIR = Path(__file__).parent / "lang"


def pet_exp_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("exp_table_id", "expTableId", "EXP Table ID"),
            offset_column("data_offset", "dataOffset", "Data Offset"),
            size_column("data_size", "dataSize", "Data Size"),
        ],
        parse_petexpoffset_records,
    )


class PetExpHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("expTableId", "EXP Table ID"), "num", sort_key="exp_table_id"),
            Column(cols.get("maxLevel", "Max Level"), "num", sort_key="max_level"),
            Column(cols.get("level", "Level"), "num", sort_key="level"),
            Column(cols.get("requiredExp", "Required EXP"), "num", sort_key="required_exp"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/petexpoffset.dbss"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get("petexpoffset.dbss")
        if offset_raw is None:
            raise ValueError("petexpoffset.dbss companion not found.")

        return parse_petexp_records(data, offset_raw)

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        table_count = len({r["exp_table_id"] for r in records})
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records), table_count=table_count)
        rows = [
            [
                e(r["exp_table_id"]),
                e(r["max_level"]),
                e(r["level"]),
                e(r["required_exp"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
