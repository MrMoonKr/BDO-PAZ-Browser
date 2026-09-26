from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler
from _common.binary import u32
from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings

_RECORD_SIZE = 8  # u32 title_id + u32 category_id
_LANG_DIR = Path(__file__).parent / "lang"

_CATEGORIES: dict[int, str] = {
    0: "World",
    1: "Combat",
    2: "Life Skill",
    3: "Fishing",
}

def _category_label(category_id: int) -> str:
    return _CATEGORIES.get(category_id, f"Unknown ({category_id})")


def _parse(data: bytes) -> list[tuple[int, int]]:
    count = len(data) // _RECORD_SIZE
    return [
        (u32(data, i * _RECORD_SIZE), u32(data, i * _RECORD_SIZE + 4))
        for i in range(count)
    ]


class TitleCategoryBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("titleId", "Title ID"), "num", sort_key="title_id"),
            Column(cols.get("categoryId", "Cat ID"), "num", sort_key="category_id"),
            Column(cols.get("category", "Category"), sort_key="category"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(self, data: bytes, entry: PazEntry, companions: dict[str, bytes]) -> list[dict]:
        return [
            {
                "title_id": title_id,
                "category_id": category_id,
                "category": _category_label(category_id),
            }
            for title_id, category_id in _parse(data)
        ]

    def render_records_page(self, records: list[dict], page: int, page_size: int) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} records"
        rows = [
            [
                e(r["title_id"]),
                e(r["category_id"]),
                e(r["category"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
