from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.lang import handler_text, load_handler_strings
from _common.html import Column, e, icon_cell, sort_keys, table
from _common.icon_index import IconKind, icon_path
from _common.loc import is_loc_loaded
from _common.pa_text import pa_cell, pa_fields
from _common.quest.quest import quest_title_tagged
from .parser import parse_allquestlist_records


_LANG_DIR = Path(__file__).parent / "lang"


class AllQuestListBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("mainId", "Main ID"), "num", sort_key="quest_chain_id"),
            Column(cols.get("subId", "Sub ID"), "num", sort_key="quest_id"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("title", "Title"), sort_key="title"),
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

        for record in parse_allquestlist_records(data):
            row = dict(record)
            title = quest_title_tagged(record["quest_chain_id"], record["quest_id"]) if has_loc else ""
            row.update(pa_fields("title", title))
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
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records))
        if with_titles:
            meta += handler_text(self.lang, _LANG_DIR, "meta.withTitles", with_titles=with_titles)

        rows = [
            [
                e(record["quest_chain_id"]),
                e(record["quest_id"]),
                icon_cell(record["icon_path"]) if record["icon_path"] else "-",
                pa_cell(record, "title"),
            ]
            for record in slice_
        ]

        return table(meta, self._columns(), rows)
