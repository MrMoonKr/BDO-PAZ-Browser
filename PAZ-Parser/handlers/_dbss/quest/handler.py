from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler
from table_sort import TableSort, sort_order_by_values

from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags

from _common.html import Column, e, icon_cell, sort_keys, table
from _common.lang import load_handler_strings
from _bss.allquestlist.parser import parse_allquestlist_records
from .model import FamilyStat
from .parser import QuestIndex, build_quest_index, parse_quest_record


_LANG_DIR = Path(__file__).parent / "lang"
_ORDER_FILE = "allquestlist.bss"


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


def _family_stat_text(stats: list[FamilyStat]) -> str:
    """`AP +1, Weight +50 LT`; a stat with an unknown field shows its label alone."""
    parts: list[str] = []
    for stat in stats:
        value = stat["value"]
        if value is None:
            parts.append(stat["label"])
            continue
        unit = " LT" if stat["label"] == "Weight" else ""
        parts.append(f"{stat['label']} {value:+g}{unit}")
    return ", ".join(parts)


class QuestDbssHandler(PreviewHandler):

    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("displayId", "Display ID"), "num", sort_key="packed_quest_id"),
            Column(cols.get("chainId", "Chain ID"), "num", sort_key="quest_chain_id"),
            Column(cols.get("questId", "Quest ID"), "num", sort_key="quest_id"),
            Column(cols.get("category", "Category"), "num", sort_key="quest_category"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("titleName", "Title / Name"), sort_key="title"),
            Column(cols.get("condition", "Condition"), sort_key="condition_script"),
            Column(cols.get("action", "Action"), sort_key="action_script"),
            Column(cols.get("objective", "Objective"), sort_key="objective"),
            Column(cols.get("familyStat", "Family Stat"), sort_key="family_stat_text"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/{_ORDER_FILE}"]

    def _get_index(self, data: bytes, companions: dict[str, bytes]) -> QuestIndex:
        def build() -> QuestIndex:
            order_raw = companions.get(_ORDER_FILE)
            if order_raw is None:
                raise ValueError(f"{_ORDER_FILE} companion not found; it gives the record order.")
            ids = [record["packed_quest_id"] for record in parse_allquestlist_records(order_raw)]
            return build_quest_index(data, ids)

        return self._data_cache(data, "index", build)

    def _record_at(self, data: bytes, index: QuestIndex, row: int) -> dict:
        record = dict(parse_quest_record(data, index, row))
        loc_texts = _quest_loc_texts(record["quest_chain_id"], record["quest_id"])
        record["loc_texts_en"] = loc_texts
        record["title"] = _title(loc_texts)
        record["objective"] = _objective(loc_texts) or record["objective_text_kr"]
        # Empty sorts last and exports as an empty cell.
        record["family_stat_text"] = _family_stat_text(record["family_stats"]) or None
        return record

    def _records_at(self, data: bytes, companions: dict[str, bytes], rows: Iterable[int]) -> list[dict]:
        index = self._get_index(data, companions)
        return [self._record_at(data, index, row) for row in rows]

    def get_record_count(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> int:
        return len(self._get_index(data, companions))

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return self._records_at(data, companions, range(len(self._get_index(data, companions))))

    def render_data_page(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
        page: int,
        page_size: int,
    ) -> str:
        total = len(self._get_index(data, companions))
        start_row = page * page_size
        rows = range(start_row, min(total, start_row + page_size))
        return self._render_table(self._records_at(data, companions, rows), total)

    def _build_sort_order(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
        sort: TableSort,
    ) -> list[int]:
        # Keeps one value per row rather than caching every parsed record
        # (scripts run to thousands of characters) through get_records().
        index = self._get_index(data, companions)
        values = [self._record_at(data, index, row).get(sort.field) for row in range(len(index))]
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
        return self._render_table(self._records_at(data, companions, rows), len(order))

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
        index = self._get_index(data, companions)
        for row in range(len(index)):
            record = self._record_at(data, index, row)
            if q in "\t".join(str(value).lower() for value in record.values()):
                matches.append(row)

        return matches

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        return self._render_table(records[page * page_size : page * page_size + page_size], len(records))

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
                e(record["quest_category"]),
                icon_cell(record["icon_path"]),
                e(_truncate(title) if title else "-"),
                e(_truncate(record["condition_script"])),
                e(_truncate(record["action_script"])),
                e(_truncate(objective) if objective else "-"),
                e(record["family_stat_text"] or "-"),
            ])

        meta = f"{total:,} quests"
        if with_loc:
            meta += f" · {with_loc:,} with LOC type 18 text"

        return table(meta, self._columns(), rows)
