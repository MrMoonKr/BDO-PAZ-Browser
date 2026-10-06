from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.item_key import item_key_list_cell, item_key_text
from _common.lang import handler_text, load_handler_strings
from _common.pabr_offset import parse_pabr_offset_rows
from _common.offset_table import (
    OffsetColumn,
    OffsetTableHandler,
    offset_column,
    offset_records,
    size_column,
)
from .parser import parse_itemsubgroup_records


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "itemsubgroupoffset.dbss"
_LIST_PREVIEW_ITEMS = 8


def item_subgroup_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("subgroup_key", "subgroupKey", "Subgroup Key"),
            offset_column("offset", "dataOffset", "Data Offset"),
            size_column("size", "size", "Size"),
        ],
        offset_records(parse_pabr_offset_rows, "subgroup_key"),
    )


class ItemSubgroupHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("subgroupKey", "Subgroup Key"), "num", sort_key="subgroup_key"),
            Column(cols.get("entryCount", "Items"), "num", sort_key="entry_count"),
            # A list column: it would only sort by its string form.
            Column(cols.get("items", "Item Names")),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
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

        return [
            {
                "subgroup_key": subgroup.subgroup_key,
                "entry_count": len(subgroup.item_keys),
                "item_keys": list(subgroup.item_keys),
                "items": [item_key_text(key) for key in subgroup.item_keys],
            }
            for subgroup in parse_itemsubgroup_records(data, offset_raw)
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        entries = sum(record["entry_count"] for record in records)
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records), entries=entries)
        rows = [
            [
                e(record["subgroup_key"]),
                e(record["entry_count"]),
                item_key_list_cell(record["item_keys"], _LIST_PREVIEW_ITEMS),
            ]
            for record in slice_
        ]
        return table(meta, self._columns(), rows)
