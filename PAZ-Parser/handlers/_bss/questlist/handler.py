from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, icon_cell, sort_keys, table
from _common.icon_index import IconKind, icon_path
from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded, loc_lookup, loc_tagged
from _common.pa_text import pa_cell, pa_fields
from _common.quest.quest import quest_title_tagged
from .parser import parse_quest_list_records


_LANG_DIR = Path(__file__).parent / "lang"
# Each quest list has its own LOC type with the group names, keyed
# (group_key, 0, 0, 0), and each quest's condition line, keyed
# (packed_quest_id, group_key, 0, 1).
QUEST_LIST_LOC_TYPES: dict[str, int] = {
    "newquest.bss": 58,
    "mainquest.bss": 43,
    "recommendationquest.bss": 28,
    "repetitionquest.bss": 42,
}
_FIELD_GROUP_NAME = 0
_FIELD_CONDITION = 1


class QuestListBssHandler(PreviewHandler):
    def __init__(self, loc_type: int) -> None:
        self._loc_type = loc_type

    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("mainId", "Main ID"), "num", sort_key="quest_chain_id"),
            Column(cols.get("subId", "Sub ID"), "num", sort_key="quest_id"),
            Column(cols.get("groupKey", "Group Key"), "num", sort_key="group_key"),
            Column(cols.get("groupName", "Group Name"), sort_key="group_name"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("title", "Title"), sort_key="title"),
            Column(cols.get("condition", "Condition"), sort_key="condition"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records: list[dict] = []
        has_loc = is_loc_loaded()

        for record in parse_quest_list_records(data):
            row = dict(record)
            title = quest_title_tagged(record["quest_chain_id"], record["quest_id"]) if has_loc else ""
            row.update(pa_fields("title", title))
            row.update(pa_fields("group_name", loc_tagged(self._loc_type, record["group_key"], _FIELD_GROUP_NAME)))
            row.update(pa_fields("condition", loc_lookup(
                self._loc_type, record["packed_quest_id"], record["group_key"], 0, _FIELD_CONDITION,
            ).strip()))
            row["icon_path"] = icon_path(IconKind.QUEST, record["packed_quest_id"])
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
        with_titles = sum(1 for record in records if record.get("title"))
        group_count = len({record["group"] for record in records})
        meta = f"{len(records):,} quest references · {group_count:,} groups"
        if with_titles:
            meta += f" · {with_titles:,} with LOC titles"

        rows = [
            [
                e(record["quest_chain_id"]),
                e(record["quest_id"]),
                e(record["group_key"]),
                pa_cell(record, "group_name"),
                icon_cell(record["icon_path"]) if record["icon_path"] else "-",
                pa_cell(record, "title"),
                pa_cell(record, "condition"),
            ]
            for record in slice_
        ]

        return table(meta, self._columns(), rows)
