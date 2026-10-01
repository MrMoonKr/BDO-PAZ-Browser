from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import strip_pa_tags
from .parser import StringRow, parse_rows
from .text import ui_hash_text


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"


def _record(row: StringRow) -> dict:
    """One table row; the text is the loaded LOC language, else the stored Korean."""
    korean = strip_pa_tags(row.value).strip()
    return {
        "key_hash": row.key_hash,
        "sheet": row.sheet,
        "key": row.key,
        "korean": korean,
        "text": ui_hash_text(row.sheet, row.key_hash) or korean,
    }


class StringTableBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("hash", "Hash"), "num", sort_key="key_hash"),
            Column(cols.get("sheet", "Sheet"), sort_key="sheet"),
            Column(cols.get("key", "Key"), sort_key="key"),
            Column(cols.get("text", "Text"), sort_key="text"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        # Hash order by default, since the file stores its rows unsorted; a key
        # in two sheets keeps its file order (the sort is stable).
        rows = sorted(parse_rows(data), key=lambda row: row.key_hash)
        return [_record(row) for row in rows]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} strings"
        rows = [
            [
                e(f"0x{r['key_hash']:08X}"),
                e(r["sheet"]),
                e(r["key"]),
                e(r["text"] or _EMPTY),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
