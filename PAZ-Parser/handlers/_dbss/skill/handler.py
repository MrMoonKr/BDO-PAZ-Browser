from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.duration import format_duration
from _common.html import Column, e, icon_cell, join_limited, sort_keys, table, truncate
from _common.icon_index import IconKind, icon_path
from _common.lang import load_handler_strings
from _common.loc import loc_text
from _common.pabr_offset import parse_pabr_u32_offset_rows
from _common.skill import skill_name, split_skill_key
from .parser import SkillRecord, parse_skill_records


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "skilloffset.dbss"
_LOC_BUFF_DESCRIPTION = 5
# LOC type 5 stores this for buffs without a description.
_LOC_NULL = "<null>"
_EMPTY = "-"
_LIST_PREVIEW_ITEMS = 3
_SCRIPT_PREVIEW_CHARS = 80


def _buff_label(buff_id: int) -> str:
    """Buff ID and the first line of its LOC type 5 text."""
    text = loc_text(_LOC_BUFF_DESCRIPTION, buff_id)
    first_line = "" if text == _LOC_NULL else text.split("\n", 1)[0].strip()
    return f"{buff_id} {first_line}" if first_line else str(buff_id)


def _skill_label(skill_key: int) -> str:
    skill_no = split_skill_key(skill_key)[0]
    return skill_name(skill_no) or str(skill_no)


def _record_dict(record: SkillRecord) -> dict:
    return {
        "skill_key": record.skill_key,
        "skill_no": record.skill_no,
        "level": record.level,
        "icon_path": icon_path(IconKind.SKILL, record.skill_no),
        # English, then the Korean skilltype.dbss name, then the internal name.
        "name": skill_name(record.skill_no) or record.name,
        "internal_name": record.name,
        # Zero means no cooldown; None sorts last.
        "cooldown_ms": record.cooldown_ms or None,
        "cooldown": format_duration(record.cooldown_ms),
        "buff_ids": list(record.buff_ids),
        "buffs": [_buff_label(buff_id) for buff_id in record.buff_ids],
        "buff_count": len(record.buff_ids) or None,
        "next_skill_keys": list(record.next_skill_keys),
        "next_skills": [_skill_label(key) for key in record.next_skill_keys],
        "base_skill_keys": list(record.base_skill_keys),
        "base_skill": ", ".join(_skill_label(key) for key in record.base_skill_keys),
        "description_kr": record.description_kr,
        "script": record.script,
    }


class SkillOffsetHandler(PreviewHandler):
    """`skilloffset.dbss` and `skilltypeoffset.dbss`: PABR rows keyed by skill key."""

    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("offsetColumns", {})
        return [
            Column(cols.get("skillNo", "Skill No"), "num", sort_key="skill_no"),
            Column(cols.get("level", "Level"), "num", sort_key="level"),
            Column(cols.get("dbssOffset", "DBSS Offset"), "num", sort_key="dbss_offset"),
            Column(cols.get("size", "Size"), "num", sort_key="size"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records = []
        for row in parse_pabr_u32_offset_rows(data):
            skill_no, level = split_skill_key(row.entry_id)
            records.append({
                "skill_key": row.entry_id,
                "skill_no": skill_no,
                "level": level,
                "dbss_offset": row.offset,
                "size": row.size,
            })
        return records

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} offset records"
        rows = [
            [e(r["skill_no"]), e(r["level"]), e(f"0x{r['dbss_offset']:08X}"), e(r["size"])]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)


class SkillHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("skillNo", "Skill No"), "num", sort_key="skill_no"),
            Column(cols.get("level", "Level"), "num", sort_key="level"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("name", "Name"), sort_key="name"),
            Column(cols.get("cooldown", "Cooldown"), "num", sort_key="cooldown_ms"),
            Column(cols.get("buffs", "Buffs"), sort_key="buff_count"),
            Column(cols.get("nextSkills", "Next Skills")),
            Column(cols.get("baseSkill", "Base Skill"), sort_key="base_skill"),
            Column(cols.get("script", "Script"), sort_key="script"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/{_OFFSET_FILE}"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get(_OFFSET_FILE)
        if offset_raw is None:
            raise ValueError(f"{_OFFSET_FILE} companion not found.")

        # The index order is arbitrary; skill number order puts class skills first.
        records = sorted(parse_skill_records(data, offset_raw), key=lambda record: record.skill_key)
        return [_record_dict(record) for record in records]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        with_buffs = sum(1 for r in records if r["buff_ids"])
        meta = f"{len(records):,} skill ranks · {with_buffs:,} with buffs"
        rows = [
            [
                e(r["skill_no"]),
                e(r["level"]),
                icon_cell(r["icon_path"]),
                e(r["name"] or _EMPTY),
                e(r["cooldown"] or _EMPTY),
                e(join_limited(r["buffs"], _LIST_PREVIEW_ITEMS) or _EMPTY),
                e(join_limited(r["next_skills"], _LIST_PREVIEW_ITEMS) or _EMPTY),
                e(r["base_skill"] or _EMPTY),
                e(truncate(r["script"], _SCRIPT_PREVIEW_CHARS) or _EMPTY),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
