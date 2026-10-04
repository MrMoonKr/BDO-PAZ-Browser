from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.loc import loc_lookup
from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, picked_records
from .parser import parse_npcpersonality_records, parse_npcpersonalityoffset_records

_LANG_DIR = Path(__file__).parent / "lang"


def _decode_personality_type(code: int) -> str:
    major = code // 100
    name = loc_lookup(7, major)
    return name if name else f"?{major}"


def _group_str(group_id: int) -> str:
    return "-" if group_id == 0 else str(group_id)


def npc_personality_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("personality_id", "personalityId", "Personality ID"),
            offset_column("data_offset", "dataOffset", "Data Offset"),
        ],
        picked_records(parse_npcpersonalityoffset_records, ("personality_id", "data_offset")),
    )


class NpcPersonalityHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("id", "ID"), "num", sort_key="personality_id"),
            Column(cols.get("row", "Row"), "num", sort_key="row"),
            Column(cols.get("groupA", "Group A"), "num", sort_key="group_a_id"),
            Column(cols.get("groupB", "Group B"), "num", sort_key="group_b_id"),
            Column(cols.get("groupC", "Group C"), "num", sort_key="group_c_id"),
            Column(cols.get("intMin", "Int Min"), "num", sort_key="interest_min"),
            Column(cols.get("intMax", "Int Max"), "num", sort_key="interest_max"),
            Column(cols.get("favMin", "Fav Min"), "num", sort_key="favor_min"),
            Column(cols.get("favMax", "Fav Max"), "num", sort_key="favor_max"),
            Column(cols.get("horoscope", "Horoscope"), sort_key="personality_type"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records = parse_npcpersonality_records(data)
        return [
            {
                "row":                rec["row"],
                "personality_id":     rec["personality_id"],
                "group_a_id":         rec["group_a_id"],
                "unknown_04":         rec["unknown_04"],
                "group_b_id":         rec["group_b_id"],
                "unknown_08":         rec["unknown_08"],
                "group_c_id":         rec["group_c_id"],
                "unknown_0c":         rec["unknown_0c"],
                "interest_min":       rec["interest_min"],
                "interest_max":       rec["interest_max"],
                "favor_min":          rec["favor_min"],
                "favor_max":          rec["favor_max"],
                "personality_type":   rec["personality_type"],
            }
            for rec in records
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} personality records"
        rows = [
            [
                e(r["personality_id"]),
                e(r["row"]),
                e(_group_str(r["group_a_id"])),
                e(_group_str(r["group_b_id"])),
                e(_group_str(r["group_c_id"])),
                e(int(r["interest_min"])),
                e(int(r["interest_max"])),
                e(int(r["favor_min"])),
                e(int(r["favor_max"])),
                e(_decode_personality_type(r["personality_type"])),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
