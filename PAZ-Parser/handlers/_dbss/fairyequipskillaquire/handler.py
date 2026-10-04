from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.equipskill_roll import flatten_roll_rows, read_skill_loc_ids
from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, size_column
from .parser import (
    FAIRY_GRADES,
    parse_fairyequipskillaquire_records,
    parse_fairyequipskillaquireoffset_records,
)


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "fairyequipskillaquireoffset.dbss"
_CATALOG_FILE = "fairyequipskill.bss"
_LOC_TYPE = 10


def _skill_name(loc_id: int) -> str:
    if not is_loc_loaded():
        return ""

    return strip_pa_tags(loc_lookup(_LOC_TYPE, loc_id, 0, 0, 0)).strip()


def fairy_equip_skill_acquire_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("acquire_type_id", "acquireTypeId", "Acquire Type ID"),
            offset_column("data_offset", "dataOffset", "Data Offset"),
            size_column("data_size", "dataSize", "Data Size"),
            offset_column("record_start", "recordStart", "Record Start"),
        ],
        parse_fairyequipskillaquireoffset_records,
    )


class FairyEquipSkillAcquireHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("equipSkillId", "Skill ID"), "num", sort_key="equip_skill_id"),
            Column(cols.get("fairyGrade", "Fairy Grade"), sort_key="fairy_grade"),
            Column(cols.get("skillName", "Skill Name"), sort_key="skill_name"),
            Column(cols.get("chance", "Chance"), "num", sort_key="chance_pct"),
            Column(cols.get("weight", "Weight"), "num", sort_key="weight"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/{_OFFSET_FILE}", f"{folder}/{_CATALOG_FILE}"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get(_OFFSET_FILE)
        if offset_raw is None:
            raise ValueError(f"{_OFFSET_FILE} companion not found.")

        records = parse_fairyequipskillaquire_records(data, offset_raw)

        catalog_raw = companions.get(_CATALOG_FILE)
        loc_ids = read_skill_loc_ids(catalog_raw) if catalog_raw else {}
        rows = flatten_roll_rows(records, loc_ids, _skill_name)

        for row in rows:
            grade, grade_name = FAIRY_GRADES.get(row["acquire_type_id"], (0, ""))
            row["fairy_grade"] = grade
            row["grade_name"] = grade_name

        return rows

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        grades = len({r["acquire_type_id"] for r in records})
        meta = f"{len(records):,} roll entries across {grades} fairy grades"

        rows = [
            [
                e(r["equip_skill_id"]),
                e(r["grade_name"] or r["acquire_type_id"]),
                e(r["skill_name"] or r["loc_id"]),
                e(f"{round(r['chance_pct'], 2):g}%"),
                e(f"{r['weight']:,}"),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
