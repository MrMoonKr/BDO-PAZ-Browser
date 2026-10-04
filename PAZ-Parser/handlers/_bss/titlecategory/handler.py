from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler
from _common.binary import u32
from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings

_MAGIC = b"PABR"
_HEADER_SIZE = 8  # PABR magic + u32 category_count
_TRAILER_SIZE = 12  # u32 0 + u32 end_of_entries + u32 0
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
    """(title_id, category_id) for every listed title.

    PABR header with a category count, then per category in ID order a u32
    title count and that many u32 title IDs, then the 12-byte trailer whose
    end-of-entries offset must be where the lists end.
    """
    if len(data) < _HEADER_SIZE + _TRAILER_SIZE or data[:4] != _MAGIC:
        raise ValueError("titlecategory.bss does not start with a PABR header")

    end_of_entries = u32(data, len(data) - _TRAILER_SIZE + 4)
    pairs: list[tuple[int, int]] = []
    pos = _HEADER_SIZE
    for category_id in range(u32(data, 4)):
        if pos + 4 > end_of_entries:
            raise ValueError(f"titlecategory category {category_id} count runs past the lists")
        title_count = u32(data, pos)
        pos += 4
        if pos + title_count * 4 > end_of_entries:
            raise ValueError(f"titlecategory category {category_id} titles run past the lists")
        pairs.extend((u32(data, pos + index * 4), category_id) for index in range(title_count))
        pos += title_count * 4

    if pos != end_of_entries:
        raise ValueError(f"titlecategory lists end at 0x{pos:X}, trailer says 0x{end_of_entries:X}")
    return pairs


class TitleCategoryBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("titleId", "Title ID"), "num", sort_key="title_id"),
            Column(cols.get("categoryId", "Cat ID"), "num", sort_key="category_id"),
            Column(cols.get("category", "Category"), sort_key="category"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
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
