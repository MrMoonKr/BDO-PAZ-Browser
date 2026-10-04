from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.character import character_name
from _common.html import Column, e, icon_cell, sort_keys, table
from _common.lang import load_handler_strings
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, size_column
from .parser import (
    parse_pet_records,
    parse_petgrade_records_with_offsets,
    parse_petgradeoffset_records,
    parse_petoffset_records,
)


_LANG_DIR = Path(__file__).parent / "lang"


def _pet_key_text(value: int) -> str:
    return f"0x{value:04X} ({value})"


def pet_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("pet_id", "petId", "Pet ID", _pet_key_text),
            offset_column("data_offset", "dataOffset", "Data Offset"),
            size_column("data_size", "dataSize", "Data Size"),
        ],
        parse_petoffset_records,
    )


class PetGradeHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("gradeColumns", {})
        return [
            Column(cols.get("key", "Key"), "num", sort_key="key"),
            Column(cols.get("species", "Species"), "num", sort_key="species"),
            Column(cols.get("variant", "Variant"), "num", sort_key="variant"),
            Column(cols.get("grade", "Grade"), sort_key="grade"),
            Column(cols.get("dataOffset", "Data Offset"), "num", sort_key="data_offset"),
            Column(cols.get("dataSize", "Data Size"), "num", sort_key="data_size"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/petgradeoffset.dbss"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get("petgradeoffset.dbss")
        if offset_raw is None:
            raise ValueError("petgradeoffset.dbss companion not found.")

        records = parse_petgrade_records_with_offsets(data, offset_raw)
        grade_names = load_handler_strings(self.lang, _LANG_DIR).get("grades", {})
        for record in records:
            grade = record["grade"]
            record["grade_name"] = grade_names.get(str(grade), f"Unknown ({grade})")
        return records

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} pet grade records"
        rows = [
            [
                e(f"0x{r['key']:04X} ({r['key']})"),
                e(r["species"]),
                e(r["variant"]),
                e(r["grade_name"]),
                e(f"0x{r['data_offset']:08X}"),
                e(r["data_size"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)


def pet_grade_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("key", "key", "Key", _pet_key_text),
            OffsetColumn("species", "species", "Species"),
            OffsetColumn("variant", "variant", "Variant"),
            offset_column("data_offset", "dataOffset", "Data Offset"),
            size_column("data_size", "dataSize", "Data Size"),
        ],
        parse_petgradeoffset_records,
        lang_block="gradeOffsetColumns",
    )


class PetDbssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("petId", "Pet ID"), "num", sort_key="pet_id"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("name", "Name"), sort_key="display_name"),
            Column(cols.get("species", "Species ID"), "num", sort_key="species"),
            Column(cols.get("tier", "Tier"), "num", sort_key="tier"),
            Column(cols.get("skillSlots", "Skill Slots"), "num", sort_key="equip_skill_slots"),
            Column(cols.get("maxLevel", "Max Level"), "num", sort_key="max_level"),
            Column(cols.get("acquireType", "Acquire Type"), "num", sort_key="acquire_type_id"),
            Column(cols.get("equipSkillId", "Equip Skill ID"), "num", sort_key="equip_skill_id"),
            Column(cols.get("grade", "Grade"), sort_key="grade"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [
            f"{folder}/petoffset.dbss",
            f"{folder}/petgrade.dbss",
        ]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get("petoffset.dbss")
        if offset_raw is None:
            raise ValueError("petoffset.dbss companion not found.")
        grade_raw = companions.get("petgrade.dbss")
        records = parse_pet_records(data, offset_raw, grade_raw)
        strings = load_handler_strings(self.lang, _LANG_DIR)
        grade_names = strings.get("grades", {})
        for record in records:
            loc_name = character_name(record["pet_id"])
            record["pet_name"] = loc_name
            record["display_name"] = loc_name or str(record["species"])
            grade = record.get("grade")
            record["grade_name"] = grade_names.get(str(grade), str(grade) if grade is not None else "")
        return records

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        species_count = len({r["species"] for r in records})
        with_grade = sum(1 for r in records if r.get("grade") is not None)
        meta = f"{len(records):,} pets · {species_count:,} species"
        if with_grade:
            meta += f" · {with_grade:,} with grade metadata"
        rows = [
            [
                e(r["pet_id"]),
                icon_cell(r["icon_path"]),
                e(r["display_name"]),
                e(r["species"]),
                e(r["tier"]),
                e(r["equip_skill_slots"]),
                e(r["max_level"]),
                e(r["acquire_type_id"]),
                e(r["equip_skill_id"]),
                e(r["grade_name"] or "-"),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
