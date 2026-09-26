from __future__ import annotations

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from .parser import parse_petskill_records, parse_petskilloffset_records


_OFFSET_COLUMNS = [
    Column("Pet Skill ID", "num", sort_key="pet_skill_id"),
    Column("Data Offset", "num", sort_key="data_offset"),
    Column("Data Size", "num", sort_key="data_size"),
]

_COLUMNS = [
    Column("Pet Skill ID", "num", sort_key="pet_skill_id"),
    Column("Skill Group", "num", sort_key="skill_group"),
    Column("Level", "num", sort_key="level"),
    Column("Value A", "num", sort_key="raw_value_a"),
    Column("Value B", "num", sort_key="raw_value_b"),
]


class PetSkillOffsetHandler(PreviewHandler):
    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(_OFFSET_COLUMNS)

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return parse_petskilloffset_records(data)

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
                e(r["pet_skill_id"]),
                e(f"0x{r['data_offset']:08X}"),
                e(r["data_size"]),
            ]
            for r in slice_
        ]
        return table(f"{len(records):,} pet skill offset records", _OFFSET_COLUMNS, rows)


class PetSkillHandler(PreviewHandler):
    def sortable_fields(self) -> frozenset[str]:
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
                e(r["skill_group"]),
                e(r["level"]),
                e(r["raw_value_a"]),
                e(r["raw_value_b"]),
            ]
            for r in slice_
        ]
        return table(meta, _COLUMNS, rows)
