from __future__ import annotations

import html as _html
import sys
from collections.abc import Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bdo_models import PazEntry
from bdo_preview import PreviewHandler, register_handler
from _common.binary import u8, u16, u32
from _common.html import Column, header_cell, sort_keys
from _common.loc import decompress_loc
from table_sort import TableSort, sort_order_by_values


_TYPE_NAMES = {
    0: "Item text",
    1: "Title names + requirements",
    2: "Skill command text",
    4: "Territory names",
    5: "Buff descriptions",
    6: "Character names",
    7: "Zodiac sign data",
    8: "Mount skill names",
    9: "Knowledge category names",
    10: "Skill names + descriptions",
    11: "City/node names",
    12: "Territories",
    15: "Emote/pose names",
    16: "House/facility type names",
    17: "Town/node names (worker select)",
    18: "Quest text/titles",
    19: "Pet action labels",
    20: "Knowledge learned messages",
    21: "Class names + descriptions",
    22: "Worker skill names + descriptions",
    23: "NPC dialogue lines",
    25: "Quest group names",
    29: "Town/node names",
    34: "Knowledge card text",
    37: "UI string sheets",
    39: "Audio voice lines",
    44: "Central Market categories",
    52: "Item-set bonus text",
    54: "NPC gift/confession response dialogue",
    63: "Adventure log metadata",
    71: "Employee names",
    113: "Lightstone combinations",
    115: "Monster Zone Info categories",
    116: "Monster Zone Info zones",
    117: "Monster Zone Info tags",
    121: "Crystal transfusion groups",
    123: "Workshop and house uses",
}

_LocRecordMeta = tuple[int, int, int, int, int, int, int, int]

_COLUMNS = [
    Column("Id1", sort_key="str_id1"),
    Column("Id2", sort_key="str_id2"),
    Column("Id3", sort_key="str_id3"),
    Column("Id4", sort_key="str_id4"),
    Column("Type (number)", sort_key="str_type"),
    Column("Type (text)", sort_key="str_type_text"),
    Column("Text", sort_key="text"),
]
_HEADER_CELLS = "".join(header_cell(column) for column in _COLUMNS)

# Record fields that sort straight from the index tuple, by tuple position.
_META_FIELD_POSITIONS = {
    "str_type": 1,
    "str_id1": 2,
    "str_id2": 3,
    "str_id3": 4,
    "str_id4": 5,
}


def _parse_all_loc_records(raw: bytes) -> list[tuple[int, int, int, int, int, int, str]]:
    """Parse all loc records: (str_size, str_type, str_id1, str_id2, str_id3, str_id4, text)."""
    data = decompress_loc(raw)
    if data is None:
        return []

    records: list[tuple[int, int, int, int, int, int, str]] = []
    pos = 0

    while pos + 16 <= len(data):
        str_size = u32(data, pos)
        str_type = u32(data, pos + 4)
        str_id1  = u32(data, pos + 8)
        str_id2  = u16(data, pos + 12)
        str_id3  = u8(data, pos + 14)
        str_id4  = u8(data, pos + 15)

        text_start = pos + 16
        text_end   = text_start + str_size * 2

        if text_end + 4 > len(data):
            break

        text = data[text_start:text_end].decode("utf-16-le", errors="replace")
        records.append((str_size, str_type, str_id1, str_id2, str_id3, str_id4, text))
        pos = text_end + 4

    return records


def _record_to_dict(data: bytes, meta: _LocRecordMeta) -> dict:
    _, str_type, str_id1, str_id2, str_id3, str_id4, text_start, text_end = meta
    text = data[text_start:text_end].decode("utf-16-le", errors="replace")
    return {
        "str_id1": str_id1,
        "str_id2": str_id2,
        "str_id3": str_id3,
        "str_id4": str_id4,
        "str_type": str_type,
        "str_type_text": _TYPE_NAMES.get(str_type, "Unknown"),
        "text": text,
    }


class _LocIndex:
    def __init__(self, raw: bytes) -> None:
        self.data = decompress_loc(raw)
        self.records: list[_LocRecordMeta] = []
        self.search_texts: list[str] | None = None
        if self.data is None:
            return

        pos = 0
        while pos + 16 <= len(self.data):
            str_size = u32(self.data, pos)
            str_type = u32(self.data, pos + 4)
            str_id1  = u32(self.data, pos + 8)
            str_id2  = u16(self.data, pos + 12)
            str_id3  = u8(self.data, pos + 14)
            str_id4  = u8(self.data, pos + 15)
            text_start = pos + 16
            text_end = text_start + str_size * 2

            if text_end + 4 > len(self.data):
                break

            self.records.append((
                str_size,
                str_type,
                str_id1,
                str_id2,
                str_id3,
                str_id4,
                text_start,
                text_end,
            ))
            pos = text_end + 4

    def record_dict(self, index: int) -> dict:
        if self.data is None:
            return {}
        return _record_to_dict(self.data, self.records[index])

    def page(self, page: int, page_size: int) -> list[dict]:
        start = page * page_size
        end = min(start + page_size, len(self.records))
        return self.records_at(range(start, end))

    def records_at(self, indices: Sequence[int]) -> list[dict]:
        return [self.record_dict(index) for index in indices]

    def sort_values(self, field: str) -> list[object]:
        """One raw value per record for `field`, read from the index without
        building record dicts."""
        position = _META_FIELD_POSITIONS.get(field)
        if position is not None:
            return [meta[position] for meta in self.records]
        if field == "str_type_text":
            return [_TYPE_NAMES.get(meta[1], "Unknown") for meta in self.records]
        if field == "text" and self.data is not None:
            data = self.data
            return [
                data[meta[6]:meta[7]].decode("utf-16-le", errors="replace")
                for meta in self.records
            ]
        raise ValueError(f"LOC records cannot be sorted by {field!r}")

    def search(self, query: str) -> list[int]:
        if self.data is None:
            return []
        q = query.lower()
        if self.search_texts is None:
            search_texts: list[str] = []
            for meta in self.records:
                _, str_type, str_id1, str_id2, str_id3, str_id4, text_start, text_end = meta
                text = self.data[text_start:text_end].decode("utf-16-le", errors="replace")
                type_text = _TYPE_NAMES.get(str_type, "Unknown")
                search_texts.append(
                    f"{str_id1}\t{str_id2}\t{str_id3}\t{str_id4}\t{str_type}\t{type_text}\t{text}".lower()
                )
            self.search_texts = search_texts
        return [index for index, text in enumerate(self.search_texts) if q in text]


class LocHandler(PreviewHandler):

    def _index(self, data: bytes) -> _LocIndex:
        return self._data_cache(data, "index", lambda: _LocIndex(data))

    def get_record_count(self, data: bytes, entry: PazEntry, companions: dict[str, bytes]) -> int:
        return len(self._index(data).records)

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(_COLUMNS)

    def _build_sort_order(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
        sort: TableSort,
    ) -> list[int]:
        return sort_order_by_values(self._index(data).sort_values(sort.field), sort.descending)

    def render_sorted_page(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
        page: int,
        page_size: int,
        sort: TableSort,
    ) -> str:
        # Decode only the rows on this page; the order itself is an index array.
        index = self._index(data)
        order = self.sorted_order(data, entry, companions, sort)
        start = page * page_size
        records = index.records_at(order[start:start + page_size])
        return self._render_page(records, page, page_size, len(index.records))

    def render_data_page(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
        page: int,
        page_size: int,
    ) -> str:
        index = self._index(data)
        return self._render_page(index.page(page, page_size), page, page_size, len(index.records))

    def search_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
        query: str,
    ) -> list[int]:
        return self._index(data).search(query)

    def get_records(self, data: bytes, entry: PazEntry, companions: dict[str, bytes]) -> list[dict]:
        index = self._index(data)
        return [index.record_dict(i) for i in range(len(index.records))]

    def render_records_page(self, records: list[dict], page: int, page_size: int) -> str:
        total = len(records)
        start = page * page_size
        end = min(start + page_size, total)
        return self._render_page(records[start:end], page, page_size, total)

    def _render_page(self, records: list[dict], page: int, page_size: int, total: int) -> str:
        start = page * page_size
        end   = min(start + page_size, total)
        rows_html = "".join(
            f"<tr>"
            f"<td>{_html.escape(str(r['str_id1']))}</td>"
            f"<td>{_html.escape(str(r['str_id2']))}</td>"
            f"<td>{r['str_id3']}</td>"
            f"<td>{r['str_id4']}</td>"
            f"<td>{_html.escape(str(r['str_type']))}</td>"
            f"<td>{_html.escape(r['str_type_text'])}</td>"
            f"<td class='loc-text'>{_html.escape(r['text'])}</td>"
            f"</tr>"
            for r in records
        )
        return f"""
<div class="loc-view">
  <div class="loc-header">
    <span class="loc-count">Showing {start + 1:,}–{end:,} of {total:,} strings</span>
  </div>
  <table class="loc-table">
    <thead>
      <tr>{_HEADER_CELLS}</tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</div>
"""


register_handler(".loc", LocHandler())
