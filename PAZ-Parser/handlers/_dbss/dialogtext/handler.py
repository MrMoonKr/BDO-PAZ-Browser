from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, join_limited, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded
from _common.pa_text import pa_key, pa_list_cell
from _common.offset_table import (
    OffsetColumn,
    OffsetTableHandler,
    offset_column,
    offset_records,
    offset_text,
    size_column,
)
from .parser import parse_dialogtext_offset_rows, parse_dialogtext_records
from .text import line_text_tagged, plain_text, voice_name


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "dialogtextoffset.dbss"
_EMPTY = "-"
_LIST_PREVIEW_ITEMS = 3


def dialog_text_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("key", "key", "Key", offset_text),
            offset_column("dbss_offset", "dbssOffset", "DBSS Offset"),
            size_column("size", "size", "Size"),
        ],
        offset_records(parse_dialogtext_offset_rows, "key", "dbss_offset"),
    )


class DialogTextHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("name", "Name"), sort_key="name"),
            Column(cols.get("lines", "Lines"), "num", sort_key="line_count"),
            Column(cols.get("text", "Text")),
            Column(cols.get("voice", "Voice")),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/{_OFFSET_FILE}"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get(_OFFSET_FILE)
        if offset_raw is None:
            raise ValueError(f"{_OFFSET_FILE} companion not found.")

        has_loc = is_loc_loaded()
        records = []
        for pool in parse_dialogtext_records(data, offset_raw):
            voices = [voice_name(line) for line in pool.lines]
            texts = [line_text_tagged(pool, line, has_loc) for line in pool.lines]
            records.append({
                "key": pool.key,
                "name": pool.name,
                "line_count": len(pool.lines),
                "texts": [plain_text(text) for text in texts],
                pa_key("texts"): texts,
                "voices": [voice for voice in voices if voice],
            })
        return records

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        lines = sum(r["line_count"] for r in records)
        meta = f"{len(records):,} text pools · {lines:,} lines"
        rows = [
            [
                e(r["name"]),
                e(r["line_count"]),
                pa_list_cell(r[pa_key("texts")], _LIST_PREVIEW_ITEMS),
                e(join_limited(r["voices"], _LIST_PREVIEW_ITEMS) or _EMPTY),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
