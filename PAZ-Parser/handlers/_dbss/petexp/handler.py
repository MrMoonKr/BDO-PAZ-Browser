from __future__ import annotations

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, size_column
from .parser import parse_petexp_records, parse_petexpoffset_records


_COLUMNS = [
    Column("EXP Table ID", "num", sort_key="exp_table_id"),
    Column("Max Level", "num", sort_key="max_level"),
    Column("Level", "num", sort_key="level"),
    Column("Required EXP", "num", sort_key="required_exp"),
]


def pet_exp_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        None,
        [
            OffsetColumn("exp_table_id", "expTableId", "EXP Table ID"),
            offset_column("data_offset", "dataOffset", "Data Offset"),
            size_column("data_size", "dataSize", "Data Size"),
        ],
        parse_petexpoffset_records,
    )


class PetExpHandler(PreviewHandler):
    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(_COLUMNS)

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
        meta = f"{len(records):,} level thresholds · {table_count:,} EXP tables"
        rows = [
            [
                e(r["exp_table_id"]),
                e(r["max_level"]),
                e(r["level"]),
                e(r["required_exp"]),
            ]
            for r in slice_
        ]
        return table(meta, _COLUMNS, rows)
