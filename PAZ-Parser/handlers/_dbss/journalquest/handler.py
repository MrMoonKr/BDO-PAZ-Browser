from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, join_limited, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded, loc_lookup
from _common.pa_text import pa_cell, pa_fields, strip_pa_tags
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, size_column
from .parser import parse_journalquest_offset_records, parse_journalquest_records


_LANG_DIR = Path(__file__).parent / "lang"
_LIST_PREVIEW_ITEMS = 6


def _page_title(journal_cat_id: int, page_no: int) -> str:
    return strip_pa_tags(loc_lookup(18, journal_cat_id, page_no, 0, 0)).strip()


def _journal_tagged(group_id: int, entry_no: int, field_id: int) -> str:
    """LOC type 63 text of a journal entry with its PA tags, or ''."""
    return loc_lookup(63, group_id, entry_no, 0, field_id).strip()


def _journal_text(group_id: int, entry_no: int, field_id: int) -> str:
    return strip_pa_tags(_journal_tagged(group_id, entry_no, field_id)).strip()


def _offset_meta(records: list[dict]) -> str:
    groups = len({record["group_id"] for record in records})
    return f"{len(records):,} entries · {groups:,} groups"


def journal_quest_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("group_id", "group", "Group"),
            OffsetColumn("entry_no", "entry", "Entry"),
            offset_column("byte_offset", "offset", "Offset"),
            size_column("byte_size", "size", "Size"),
        ],
        parse_journalquest_offset_records,
        meta=_offset_meta,
    )


class JournalQuestDbssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("group", "Group"), "num", sort_key="group_id"),
            Column(cols.get("entry", "Entry"), "num", sort_key="entry_no"),
            Column(cols.get("journalCategoryId", "Journal Category ID"), "num", sort_key="journal_cat_id"),
            Column(cols.get("title", "Title"), sort_key="journal_title_text"),
            Column(cols.get("subtitle", "Subtitle"), sort_key="subtitle_text"),
            Column(cols.get("volume", "Volume"), sort_key="page_vol_title_text"),
            Column(cols.get("pageTitles", "Page Titles")),
            Column(cols.get("unlockCondition", "Unlock Condition"), sort_key="unlock_condition_text"),
            Column(cols.get("pages", "Pages"), "num", sort_key="page_count"),
            Column(cols.get("recordBook", "Record Book"), sort_key="is_record_book"),
            Column(cols.get("combineModel", "Combine Model"), sort_key="combine_model"),
            Column(cols.get("staticModel", "Static Model"), sort_key="static_model"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/journalquestoffset.dbss"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get("journalquestoffset.dbss")
        if offset_raw is None:
            raise ValueError("journalquestoffset.dbss companion not found - cannot parse records.")

        records = parse_journalquest_records(data, offset_raw)
        has_loc = is_loc_loaded()

        for record in records:
            title_en = _journal_text(record["group_id"], record["entry_no"], 0) if has_loc else ""
            subtitle_en = _journal_text(record["group_id"], record["entry_no"], 1) if has_loc else ""
            unlock_tagged = _journal_tagged(record["group_id"], record["entry_no"], 2) if has_loc else ""
            unlock_en = strip_pa_tags(unlock_tagged).strip()
            volume_en = _journal_text(record["group_id"], record["entry_no"], 3) if has_loc else ""
            page_titles: list[str] = []
            for page_ref in record["page_refs"]:
                if has_loc:
                    title = _page_title(page_ref["journal_cat_id"], page_ref["page_no"])
                else:
                    title = ""
                page_titles.append(title or f"{page_ref['journal_cat_id']}:{page_ref['page_no']}")
            record["journal_title_en"] = title_en
            record["subtitle_en"] = subtitle_en
            record["page_vol_title_en"] = volume_en
            record["unlock_condition_en"] = unlock_en
            record["journal_title_text"] = title_en or record["journal_title"]
            record["subtitle_text"] = subtitle_en or record["subtitle"]
            record["page_vol_title_text"] = volume_en or record["page_vol_title"]
            # Unlock conditions name their quests in game colours, in LOC and in Korean.
            record.update(
                pa_fields("unlock_condition_text", unlock_tagged if unlock_en else record["unlock_condition"])
            )
            record["page_titles"] = page_titles
            record["page_titles_text"] = ", ".join(page_titles)

        return records

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        values = load_handler_strings(self.lang, _LANG_DIR).get("values", {})
        yes, no = values.get("yes", "Yes"), values.get("no", "No")
        pages = sum(r["page_count"] for r in records)
        groups = len({r["group_id"] for r in records})
        meta = f"{len(records):,} journal entries · {groups:,} groups · {pages:,} pages"
        rows = [
            [
                e(r["group_id"]),
                e(r["entry_no"]),
                e(r["journal_cat_id"]),
                e(r["journal_title_text"]),
                e(r["subtitle_text"]),
                e(r["page_vol_title_text"]),
                e(join_limited(r["page_titles"], _LIST_PREVIEW_ITEMS)),
                pa_cell(r, "unlock_condition_text"),
                e(r["page_count"]),
                e(yes if r["is_record_book"] else no),
                e(r["combine_model"]),
                e(r["static_model"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
