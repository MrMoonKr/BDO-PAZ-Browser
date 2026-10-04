from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings
from .parser import parse_fairyfeedenchantfailcount_records


_LANG_DIR = Path(__file__).parent / "lang"


class FairyFeedEnchantFailCountBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        # Every entry field is unknown_*: kept for search and export, not shown.
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("record", "Record"), "num", sort_key="record"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return parse_fairyfeedenchantfailcount_records(data)

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        record_count = len({record["record"] for record in records})
        meta = f"{len(records):,} entries across {record_count} records"

        rows = [[e(record["record"])] for record in slice_]

        return table(meta, self._columns(), rows)
