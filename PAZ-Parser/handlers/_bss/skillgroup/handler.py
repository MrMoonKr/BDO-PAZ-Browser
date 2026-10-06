from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, icon_cell, sort_keys, table, text_list_cell
from _common.icon_index import IconKind, icon_path
from _common.lang import handler_text, load_handler_strings
from _common.pa_text import pa_cell, pa_fields
from _common.skill import skill_name, skill_name_tagged, split_skill_key
from .parser import SkillGroup, parse_skillgroup_records


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"
_LIST_PREVIEW_ITEMS = 4


def _record_dict(group: SkillGroup) -> dict:
    skill_nos = [split_skill_key(key)[0] for key in group.skill_keys]
    # The first rank stands for the group, as in the skill window.
    first = skill_nos[0] if skill_nos else None
    return {
        "group_no": group.group_no,
        "icon_path": icon_path(IconKind.SKILL, first) if first is not None else "",
        **pa_fields("name", skill_name_tagged(first) if first is not None else ""),
        "ranks": len(group.skill_keys),
        "skill_keys": list(group.skill_keys),
        "skill_nos": skill_nos,
        "skills": [f"{skill_no} {skill_name(skill_no)}".rstrip() for skill_no in skill_nos],
    }


class SkillGroupBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR)["columns"]
        return [
            Column(cols["group"], "num", sort_key="group_no"),
            Column(cols["icon"], sort_key="icon_path"),
            Column(cols["name"], sort_key="name"),
            Column(cols["ranks"], "num", sort_key="ranks"),
            Column(cols["skills"]),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return [_record_dict(group) for group in parse_skillgroup_records(data)]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records))
        rows = [
            [
                e(r["group_no"]),
                icon_cell(r["icon_path"]),
                pa_cell(r, "name"),
                e(r["ranks"]),
                text_list_cell(r["skills"], _LIST_PREVIEW_ITEMS) or _EMPTY,
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
