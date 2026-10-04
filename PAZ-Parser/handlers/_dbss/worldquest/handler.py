from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings
from .parser import parse_worldquest_records


_LANG_DIR = Path(__file__).parent / "lang"


class WorldQuestDbssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("count", "Count"), "num", sort_key="count"),
            Column(cols.get("status", "Status"), sort_key="status"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return parse_worldquest_records(data)

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        count = records[0]["count"] if records else 0
        meta = f"Header count: {count:,}"
        rows = [
            [
                e(r["count"]),
                e(r["status"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
