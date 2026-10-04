from __future__ import annotations

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, size_column
from .parser import parse_petskill_records, parse_petskilloffset_records


_COLUMNS = [
    Column("Pet Skill ID", "num", sort_key="pet_skill_id"),
    Column("Level", "num", sort_key="level"),
    Column("Value A", "num", sort_key="raw_value_a"),
    Column("Value B", "num", sort_key="raw_value_b"),
]


def pet_skill_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        None,
        [
            OffsetColumn("pet_skill_id", "petSkillId", "Pet Skill ID"),
            offset_column("data_offset", "dataOffset", "Data Offset"),
            size_column("data_size", "dataSize", "Data Size"),
        ],
        parse_petskilloffset_records,
    )


class PetSkillHandler(PreviewHandler):
    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(_COLUMNS)

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/petskilloffset.dbss"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get("petskilloffset.dbss")
        if offset_raw is None:
            raise ValueError("petskilloffset.dbss companion not found.")
        return parse_petskill_records(data, offset_raw)

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        skill_count = len({r["pet_skill_id"] for r in records})
        meta = f"{skill_count:,} pet skills · {len(records):,} level rows"
        rows = [
            [
                e(r["pet_skill_id"]),
                e(r["level"]),
                e(r["raw_value_a"]),
                e(r["raw_value_b"]),
            ]
            for r in slice_
        ]
        return table(meta, _COLUMNS, rows)
