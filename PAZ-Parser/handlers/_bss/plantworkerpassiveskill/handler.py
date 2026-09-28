from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, icon_cell, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags
from .display import format_effect, format_effect_type
from .parser import parse_plantworkerpassiveskill_records


_LANG_DIR = Path(__file__).parent / "lang"


def _loc_skill_text(skill_id: int, field_id: int) -> str:
    if not is_loc_loaded():
        return ""

    return strip_pa_tags(loc_lookup(22, skill_id, 0, 0, field_id)).strip()


def _row(record: dict) -> list[str]:
    effect = format_effect(
        record["effect_type"],
        record["effect_target"],
        record["effect_value_a"],
        record["effect_value_b"],
    )
    return [
        e(record["skill_id"]),
        icon_cell(record["icon_path"]),
        e(record.get("display_name") or "-"),
        e(record.get("display_description") or "-"),
        e(record["acquisition_weight"]),
        e(format_effect_type(record["effect_type"])),
        e(effect.target),
        e(effect.effect_a),
        e(effect.effect_b),
    ]


class PlantWorkerPassiveSkillBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("skillId", "Skill ID"), "num", sort_key="skill_id"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("name", "Name"), sort_key="display_name"),
            Column(cols.get("description", "Description"), sort_key="display_description"),
            Column(cols.get("weight", "Weight"), "num", sort_key="acquisition_weight"),
            Column(cols.get("effectType", "Effect Type"), sort_key="effect_type"),
            Column(cols.get("target", "Target"), sort_key="effect_target"),
            Column(cols.get("effectA", "Effect A"), "num", sort_key="effect_value_a"),
            Column(cols.get("effectB", "Effect B"), "num", sort_key="effect_value_b"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records: list[dict] = []
        for record in parse_plantworkerpassiveskill_records(data):
            row = dict(record)
            row["display_name"] = (
                _loc_skill_text(row["skill_id"], 0) or row["inline_name"]
            )
            row["display_description"] = (
                _loc_skill_text(row["skill_id"], 1) or row["inline_description"]
            )
            # 0 means the skill has no second value. None renders a dash and sorts last.
            row["effect_value_b"] = row["effect_value_b"] or None
            records.append(row)
        return records

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        localized = sum(
            1
            for record in records
            if record.get("display_name") != record.get("inline_name")
            or record.get("display_description") != record.get("inline_description")
        )

        meta = f"{len(records):,} worker passive skill records"
        if localized:
            meta += f" · {localized:,} with LOC text"

        rows = [_row(record) for record in slice_]
        return table(meta, self._columns(), rows)
