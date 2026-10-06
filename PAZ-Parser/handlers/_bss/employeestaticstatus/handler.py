from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.character import character_name, character_title
from _common.html import Column, e, icon_cell, sort_keys, table
from _common.lang import handler_text, load_handler_strings
from _bss.stringtable.parser import GAME_SHEET
from _bss.stringtable.text import STRINGTABLE_FILE, KeyHashes, ui_key_hashes, ui_key_text
from .display import stat_text, weight_text
from .parser import STAT_FIELDS, parse_employeestaticstatus_records


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"
# `job` values; the second list in the file holds the First Mates.
_JOB_KEYS = {0: "sailor", 1: "firstMate"}
# The sailor preset Lua picks a First Mate's skill text by character key;
# Cleia's ability 17 is the 10% and Tranan's ability 18 the auto-repair switch.
_FIRST_MATE_SKILL_KEYS = {
    62167: "LUA_CAPTAIN_SAILOR_PRESET_SKILL_DESC_02",
    62168: "LUA_CAPTAIN_SAILOR_PRESET_SKILL_DESC_03",
    62169: "LUA_CAPTAIN_SAILOR_PRESET_SKILL_DESC_01",
}


def _first_mate_skill(hashes: KeyHashes, character_id: int) -> str:
    """The skill text the sailor window shows for this character, or '' for everyone else."""
    key = _FIRST_MATE_SKILL_KEYS.get(character_id)
    return ui_key_text(hashes, GAME_SHEET, key) if key else ""


class EmployeeStaticStatusBssHandler(PreviewHandler):
    def _strings(self) -> dict:
        return load_handler_strings(self.lang, _LANG_DIR)

    def _columns(self) -> list[Column]:
        cols = self._strings()["columns"]
        return [
            Column(cols["employeeKey"], "num", sort_key="employee_key"),
            Column(cols["level"], "num", sort_key="level"),
            Column(cols["icon"], sort_key="icon_path"),
            Column(cols["name"], sort_key="name"),
            Column(cols["title"], sort_key="title"),
            Column(cols["role"], sort_key="job_label"),
            Column(cols["characterId"], "num", sort_key="character_id"),
            *(Column(cols[field], "num", sort_key=field) for field in STAT_FIELDS.values()),
            Column(cols["maxCondition"], "num", sort_key="max_condition"),
            Column(cols["appetite"], "num", sort_key="appetite"),
            Column(cols["cabinCost"], "num", sort_key="cabin_cost"),
            Column(cols["weight"], "num", sort_key="weight"),
            Column(cols["firstMateSkill"], sort_key="first_mate_skill"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/{STRINGTABLE_FILE}"]

    def _job_label(self, job: int) -> str:
        key = _JOB_KEYS.get(job)
        return self._strings()["jobs"][key] if key else str(job)

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        hashes = ui_key_hashes(companions.get(STRINGTABLE_FILE), [GAME_SHEET])
        return [
            {
                **record,
                "name": character_name(record["character_id"]),
                "title": character_title(record["character_id"]),
                "job_label": self._job_label(record["job"]),
                "first_mate_skill": _first_mate_skill(hashes, record["character_id"]),
            }
            for record in parse_employeestaticstatus_records(data)
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        employees = len({record["employee_key"] for record in records})
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records), employees=employees)

        rows = [
            [
                e(record["employee_key"]),
                e(record["level"]),
                icon_cell(record["icon_path"] or f"#{record['icon_index']}"),
                e(record["name"] or _EMPTY),
                e(record["title"] or _EMPTY),
                e(record["job_label"]),
                e(record["character_id"]),
                *(e(stat_text(record[field])) for field in STAT_FIELDS.values()),
                e(record["max_condition"]),
                e(record["appetite"]),
                e(record["cabin_cost"]),
                e(weight_text(record["weight"])),
                e(record["first_mate_skill"] or _EMPTY),
            ]
            for record in slice_
        ]

        return table(meta, self._columns(), rows)
