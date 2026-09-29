from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, icon_cell, sort_keys, table
from _common.lang import load_handler_strings
from _common.skill import skill_name
from .parser import SkillTypeRecord, parse_skilltype_records


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "skilltypeoffset.dbss"
_EMPTY = "-"


def _record_dict(record: SkillTypeRecord, kind_labels: dict[str, str]) -> dict:
    return {
        "skill_key": record.skill_key,
        "skill_no": record.skill_no,
        "icon_path": record.icon_path,
        # English first, then the Korean source.
        "name": skill_name(record.skill_no) or record.name_kr,
        "name_kr": record.name_kr,
        "group_name_kr": record.group_name_kr,
        "kind": record.kind,
        "kind_label": kind_labels.get(str(record.kind), str(record.kind)),
    }


class SkillTypeHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("skillNo", "Skill No"), "num", sort_key="skill_no"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("name", "Name"), sort_key="name"),
            Column(cols.get("kind", "Kind"), sort_key="kind"),
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

        kind_labels = load_handler_strings(self.lang, _LANG_DIR).get("kind", {})
        # The index order is arbitrary; skill number order puts class skills first.
        records = sorted(parse_skilltype_records(data, offset_raw), key=lambda record: record.skill_key)
        return [_record_dict(record, kind_labels) for record in records]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        with_icon = sum(1 for r in records if r["icon_path"])
        meta = f"{len(records):,} skills · {with_icon:,} with an icon"
        rows = [
            [
                e(r["skill_no"]),
                icon_cell(r["icon_path"]),
                e(r["name"] or _EMPTY),
                e(r["kind_label"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
