from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler
from table_sort import TableSort, sort_order_by_values

from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags

from _common.html import Column, e, icon_cell, sort_keys, table
from _common.lang import load_handler_strings
from .parser import QuestIndex, build_quest_index, parse_quest_record


_LANG_DIR = Path(__file__).parent / "lang"


def _truncate(text: str, max_len: int = 140) -> str:
    return text if len(text) <= max_len else text[:max_len] + "..."


def _quest_loc_texts(quest_chain_id: int, quest_id: int) -> list[str]:
    if not is_loc_loaded():
        return []

    seen: set[str] = set()
    texts: list[str] = []
    for str_id4 in range(10):
        text = loc_lookup(18, quest_chain_id, quest_id, 0, str_id4)
        clean = strip_pa_tags(text).strip()
        if clean and clean not in seen:
            seen.add(clean)
            texts.append(clean)
    return texts


def _title(loc_texts: list[str]) -> str:
    return loc_texts[0] if loc_texts else ""


def _objective(loc_texts: list[str]) -> str:
    return loc_texts[3] if len(loc_texts) > 3 else ""


class QuestDbssHandler(PreviewHandler):

    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("displayId", "Display ID"), "num", sort_key="packed_quest_id"),
            Column(cols.get("chainId", "Chain ID"), "num", sort_key="quest_chain_id"),
            Column(cols.get("questId", "Quest ID"), "num", sort_key="quest_id"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("titleName", "Title / Name"), sort_key="title"),
            Column(cols.get("condition", "Condition"), sort_key="condition_script"),
            Column(cols.get("action", "Action"), sort_key="action_script"),
            Column(cols.get("objective", "Objective"), sort_key="objective"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def _get_index(self, data: bytes) -> QuestIndex:
        return self._data_cache(data, "index", lambda: build_quest_index(data))

    def _record_at(self, data: bytes, index: QuestIndex, row: int) -> dict | None:
        """Parse one index row, or None when its fixed strings do not parse."""
        canonical_id = index.canonical_quest_ids[row] if row < len(index.canonical_quest_ids) else 0
        start = index.record_starts[row]
        if start is None:
            return self._partial_record(row, index, canonical_id)

        parsed = parse_quest_record(data, row, start, index.record_ends[row], canonical_id)
        if parsed is None:
            return None

        record = dict(parsed)
        loc_texts = _quest_loc_texts(record["quest_chain_id"], record["quest_id"])
        record["loc_texts_en"] = loc_texts
        record["title"] = _title(loc_texts)
        record["objective"] = _objective(loc_texts) or record["objective_text_kr"]
        return record

    def _records_at(self, data: bytes, rows: Iterable[int]) -> list[dict]:
        index = self._get_index(data)
        records = (self._record_at(data, index, row) for row in rows)
        return [record for record in records if record is not None]

    def get_record_count(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> int:
        return len(self._get_index(data).record_starts)

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return self._records_at(data, range(len(self._get_index(data).record_starts)))

    def render_data_page(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
        page: int,
        page_size: int,
    ) -> str:
        total = len(self._get_index(data).record_starts)
        start_row = page * page_size
        rows = range(start_row, min(total, start_row + page_size))
        return self._render_table(self._records_at(data, rows), total)

    def _build_sort_order(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
        sort: TableSort,
    ) -> list[int]:
        # Keeps one value per row rather than caching every parsed record
        # (scripts run to thousands of characters) through get_records().
        index = self._get_index(data)
        values: list[object] = []
        for row in range(len(index.record_starts)):
            record = self._record_at(data, index, row)
            values.append(None if record is None else record.get(sort.field))
        return sort_order_by_values(values, sort.descending)

    def render_sorted_page(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
        page: int,
        page_size: int,
        sort: TableSort,
    ) -> str:
        order = self.sorted_order(data, entry, companions, sort)
        start = page * page_size
        rows = order[start : start + page_size]
        return self._render_table(self._records_at(data, rows), len(order))

    def search_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
        query: str,
    ) -> list[int]:
        q = query.lower()
        if not q:
            return []

        matches: list[int] = []
        index = self._get_index(data)
        for row in range(len(index.record_starts)):
            record = self._record_at(data, index, row)
            if record and q in "\t".join(str(value).lower() for value in record.values()):
                matches.append(row)

        return matches

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        return self._render_table(records[page * page_size : page * page_size + page_size], len(records))

    def _partial_record(self, row: int, index: QuestIndex, canonical_id: int = 0) -> dict:
        cid = canonical_id or 0
        chain_id = cid & 0xFFFF
        quest_id  = cid >> 16
        loc_texts = _quest_loc_texts(chain_id, quest_id) if cid else []
        return {
            "row": row,
            "offset": "",
            "size": "",
            "packed_quest_id": cid or "",
            "quest_chain_id": chain_id or "",
            "quest_id": quest_id or "",
            "condition_script": "",
            "action_script": "",
            "objective_text_kr": "",
            "icon_path": index.icon_paths[row] if row < len(index.icon_paths) else "",
            "loc_texts_en": loc_texts,
            "title": _title(loc_texts),
            "objective": _objective(loc_texts),
            "parse_status": "Icon-only",
        }

    def _render_table(self, records: list[dict], total: int) -> str:
        rows: list[list] = []
        with_loc = 0

        for record in records:
            if record.get("loc_texts_en"):
                with_loc += 1
            title = record["title"]
            objective = record["objective"]

            rows.append([
                e(record["packed_quest_id"]),
                e(record["quest_chain_id"]),
                e(record["quest_id"]),
                icon_cell(record["icon_path"]),
                e(_truncate(title) if title else "-"),
                e(_truncate(record["condition_script"])),
                e(_truncate(record["action_script"])),
                e(_truncate(objective) if objective else "-"),
            ])

        meta = f"{total:,} quests"
        if with_loc:
            meta += f" · {with_loc:,} with LOC type 18 text"
        icon_only = sum(1 for record in records if record.get("parse_status") == "Icon-only")
        if icon_only:
            meta += f" · {icon_only:,} icon-only on this page"

        return table(meta, self._columns(), rows)
