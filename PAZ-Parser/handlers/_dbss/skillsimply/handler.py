from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.class_type import ALL_CLASSES_MASK, class_name, class_types_in_mask
from _common.html import Column, e, flag_cell, icon_cell, sort_keys, table, text_list_cell
from _common.icon_index import IconKind, icon_path
from _common.lang import handler_text, load_handler_strings
from _common.pa_text import pa_cell, pa_fields
from _common.skill import skill_name, skill_name_tagged
from .parser import SkillSimplyRecord, parse_skillsimply_records


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "skillsimplyoffset.dbss"
_EMPTY = "-"
_LIST_PREVIEW_ITEMS = 3
# weapon_type of every Awakening weapon skill, whatever the class.
_AWAKENING_WEAPON_TYPE = 57


def _skill_label(skill_no: int) -> str:
    return skill_name(skill_no) or str(skill_no)


def _classes(class_mask: int, all_label: str) -> str:
    if class_mask == ALL_CLASSES_MASK:
        return all_label
    return ", ".join(class_name(class_type) for class_type in class_types_in_mask(class_mask))


def _weapon(record: SkillSimplyRecord, labels: dict[str, str]) -> str:
    """Main, Sub or Awakening; empty for skills without a weapon."""
    if record.uses_main_weapon:
        return labels.get("main", "Main")
    if record.uses_sub_weapon:
        return labels.get("sub", "Sub")
    if record.weapon_type == _AWAKENING_WEAPON_TYPE:
        return labels.get("awakening", "Awakening")
    return ""


def _record_dict(record: SkillSimplyRecord, strings: dict) -> dict:
    kind_labels = strings.get("kind", {})
    branch_labels = strings.get("branch", {})
    return {
        "skill_key": record.skill_key,
        "skill_no": record.skill_no,
        "level": record.level,
        "icon_path": icon_path(IconKind.SKILL, record.skill_no),
        **pa_fields("name", skill_name_tagged(record.skill_no)),
        "class_mask": record.class_mask,
        "classes": _classes(record.class_mask, strings.get("allClasses", "All")),
        "kind": record.kind,
        "kind_label": kind_labels.get(str(record.kind), str(record.kind)),
        # Zero means neither branch; None sorts last.
        "branch": record.branch or None,
        "branch_label": branch_labels.get(str(record.branch), str(record.branch)) if record.branch else "",
        "weapon_type": record.weapon_type,
        "weapon": _weapon(record, strings.get("weapon", {})),
        "is_fusion": record.is_fusion,
        "can_quick_slot": record.can_quick_slot,
        # Zero means no requirement; None sorts last.
        "need_level": record.need_level or None,
        "need_skill_point": record.need_skill_point or None,
        "need_skill_nos": list(record.need_skill_nos),
        "need_skills": [_skill_label(no) for no in record.need_skill_nos],
        "previous_rank_no": record.previous_rank_no or None,
        "previous_rank": _skill_label(record.previous_rank_no) if record.previous_rank_no else "",
        "next_rank_keys": list(record.next_rank_keys),
        "first_rank_key": record.first_rank_key,
        "exclusive_skill_nos": list(record.exclusive_skill_nos),
        "exclusive_skills": [_skill_label(no) for no in record.exclusive_skill_nos],
        "base_skill_keys": list(record.base_skill_keys),
    }


class SkillSimplyHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("skillNo", "Skill No"), "num", sort_key="skill_no"),
            Column(cols.get("level", "Level"), "num", sort_key="level"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("name", "Name"), sort_key="name"),
            Column(cols.get("classes", "Classes"), sort_key="classes"),
            Column(cols.get("kind", "Kind"), sort_key="kind"),
            Column(cols.get("branch", "Branch"), sort_key="branch"),
            Column(cols.get("weapon", "Weapon"), sort_key="weapon"),
            Column(cols.get("quickSlot", "Quick Slot"), sort_key="can_quick_slot"),
            Column(cols.get("needLevel", "Required Level"), "num", sort_key="need_level"),
            Column(cols.get("needSkillPoint", "Skill Points"), "num", sort_key="need_skill_point"),
            Column(cols.get("needSkills", "Required Skills")),
            Column(cols.get("previousRank", "Previous Rank"), sort_key="previous_rank"),
            Column(cols.get("exclusiveSkills", "Exclusive Skills")),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
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

        strings = load_handler_strings(self.lang, _LANG_DIR)
        # The index order is arbitrary; skill number order puts class skills first.
        records = sorted(parse_skillsimply_records(data, offset_raw), key=lambda record: record.skill_key)
        return [_record_dict(record, strings) for record in records]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        # Neither every class (item and event skills) nor none (ship and item effects).
        class_skills = sum(1 for r in records if r["class_mask"] not in (0, ALL_CLASSES_MASK))
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records), class_skills=class_skills)
        rows = [
            [
                e(r["skill_no"]),
                e(r["level"]),
                icon_cell(r["icon_path"]),
                pa_cell(r, "name"),
                e(r["classes"] or _EMPTY),
                e(r["kind_label"]),
                e(r["branch_label"] or _EMPTY),
                e(r["weapon"] or _EMPTY),
                flag_cell(r["can_quick_slot"]),
                e(r["need_level"] or _EMPTY),
                e(r["need_skill_point"] or _EMPTY),
                text_list_cell(r["need_skills"], _LIST_PREVIEW_ITEMS) or _EMPTY,
                e(r["previous_rank"] or _EMPTY),
                text_list_cell(r["exclusive_skills"], _LIST_PREVIEW_ITEMS) or _EMPTY,
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
