from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, icon_cell, sort_keys, table
from _common.lang import handler_text, load_handler_strings
from _common.quest.quest import quest_title
from .parser import parse_questjournalvideoinfo_records


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"


class QuestJournalVideoInfoBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR)["columns"]
        return [
            Column(cols["mainId"], "num", sort_key="quest_chain_id"),
            Column(cols["subId"], "num", sort_key="quest_id"),
            Column(cols["artwork"], sort_key="artwork_path"),
            Column(cols["title"], sort_key="title"),
            Column(cols["video"], sort_key="video_path"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        # The file holds no text, so without LOC the title is empty.
        return [
            {**record, "title": quest_title(record["quest_chain_id"], record["quest_id"])}
            for record in parse_questjournalvideoinfo_records(data)
        ]

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
                e(r["quest_chain_id"]),
                e(r["quest_id"]),
                icon_cell(r["artwork_path"]) if r["artwork_path"] else _EMPTY,
                e(r["title"] or _EMPTY),
                e(r["video_path"] or _EMPTY),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
