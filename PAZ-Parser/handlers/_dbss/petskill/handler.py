from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import handler_text, load_handler_strings
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, size_column
from .parser import parse_petskill_records, parse_petskilloffset_records


_LANG_DIR = Path(__file__).parent / "lang"


def pet_skill_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("pet_skill_id", "petSkillId", "Pet Skill ID"),
            offset_column("data_offset", "dataOffset", "Data Offset"),
            size_column("data_size", "dataSize", "Data Size"),
        ],
        parse_petskilloffset_records,
    )


class PetSkillHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("petSkillId", "Pet Skill ID"), "num", sort_key="pet_skill_id"),
            Column(cols.get("level", "Level"), "num", sort_key="level"),
            Column(cols.get("valueA", "Value A"), "num", sort_key="raw_value_a"),
            Column(cols.get("valueB", "Value B"), "num", sort_key="raw_value_b"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

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
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", skill_count=skill_count, count=len(records))
        rows = [
            [
                e(r["pet_skill_id"]),
                e(r["level"]),
                e(r["raw_value_a"]),
                e(r["raw_value_b"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
