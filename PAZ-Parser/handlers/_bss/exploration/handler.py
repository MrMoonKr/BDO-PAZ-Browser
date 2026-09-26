from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags
from .parser import parse_exploration_records


_LANG_DIR = Path(__file__).parent / "lang"


def _knowledge_text(knowledge_id: int, str_id4: int) -> str:
    return strip_pa_tags(loc_lookup(34, knowledge_id, 0, 0, str_id4))


class ExplorationBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("knowledgeId", "Knowledge ID"), "num", sort_key="knowledge_id"),
            Column(cols.get("knowledgeName", "Knowledge Name"), sort_key="knowledge_name"),
            Column(cols.get("groupId", "Group ID"), "num", sort_key="group_id"),
            Column(cols.get("enabled", "Enabled"), "num", sort_key="enabled"),
            Column(cols.get("anchorId", "Anchor ID"), "num", sort_key="anchor_id_a"),
            Column(cols.get("radius", "Radius"), "num", sort_key="radius"),
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
        has_loc = is_loc_loaded()

        for record in parse_exploration_records(data):
            row = dict(record)
            knowledge_id = record["knowledge_id"]
            row["knowledge_name"] = _knowledge_text(knowledge_id, 0) if has_loc else ""
            row["description"] = _knowledge_text(knowledge_id, 1) if has_loc else ""
            row["hint"] = _knowledge_text(knowledge_id, 2) if has_loc else ""
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
        with_names = sum(1 for record in records if record.get("knowledge_name"))
        meta = f"{len(records):,} exploration entries"
        if with_names:
            meta += f" · {with_names:,} LOC names"

        rows = [
            [
                e(record["knowledge_id"]),
                e(record.get("knowledge_name") or "-"),
                e(record["group_id"]),
                e(record["enabled"]),
                e(record["anchor_id_a"]),
                e(f"{record['radius']:.2f}"),
            ]
            for record in slice_
        ]

        return table(meta, self._columns(), rows)
