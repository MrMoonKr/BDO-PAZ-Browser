from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table, text_list_cell
from _common.lang import handler_text, load_handler_strings
from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags
from _common.quest.quest import quest_title
from .parser import parse_questgroup_records


_LANG_DIR = Path(__file__).parent / "lang"
_LIST_PREVIEW_ITEMS = 8


def _group_name_en(group_id: int) -> str:
    return strip_pa_tags(loc_lookup(25, group_id)).strip()


class QuestGroupDbssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR)["columns"]
        return [
            Column(cols["groupId"], "num", sort_key="group_id"),
            Column(cols["name"], sort_key="name"),
            Column(cols["quests"], "num", sort_key="quest_count"),
            Column(cols["questTitles"]),
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

        for record in parse_questgroup_records(data):
            name_en = _group_name_en(record["group_id"]) if has_loc else ""
            quest_titles: list[str] = []
            for quest in record["quests"]:
                title = quest_title(quest["group_id"], quest["quest_no"]) if has_loc else ""
                quest_titles.append(title or f"{quest['group_id']}:{quest['quest_no']}")

            records.append({
                "row": record["row"],
                "offset": record["offset"],
                "size": record["size"],
                "group_id": record["group_id"],
                "name_kr": record["name_kr"],
                "name_en": name_en,
                "name": name_en or record["name_kr"],
                "quest_count": record["quest_count"],
                "quest_titles": quest_titles,
                "quest_titles_text": ", ".join(quest_titles),
            })

        return records

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start:start + page_size]
        total_links = sum(r["quest_count"] for r in records)
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records), total_links=total_links)
        rows = [
            [
                e(r["group_id"]),
                e(r["name"]),
                e(r["quest_count"]),
                text_list_cell(r["quest_titles"], _LIST_PREVIEW_ITEMS),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
