from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.binary import parse_offset_table
from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings


_LANG_DIR = Path(__file__).parent / "lang"


class TitleOffsetHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("titleId", "Title ID"), "num", sort_key="title_id"),
            Column(cols.get("offset", "Offset"), "num", sort_key="offset"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_map = parse_offset_table(data)
        return [
            {"title_id": title_id, "offset": offset}
            for title_id, (offset, size) in sorted(offset_map.items())
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} entries"
        rows = [
            [e(r["title_id"]), e(f"0x{r['offset']:08X}")]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
