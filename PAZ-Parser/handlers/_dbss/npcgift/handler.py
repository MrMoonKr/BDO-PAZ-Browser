from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.loc import is_loc_loaded
from _common.html import Column, e, icon_cell, sort_keys, table
from _common.icon_index import IconKind, icon_path
from _common.item_grade import item_grade, item_grade_tagged
from _common.lang import handler_text, load_handler_strings
from _common.pa_text import pa_cell, pa_key
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, size_column
from .parser import (
    parse_gift_offset_records,
    parse_npcgift_records,
    parse_npcgiftdata_records,
)


_LANG_DIR = Path(__file__).parent / "lang"


def _read_gift_offsets(data: bytes) -> list[dict]:
    return [dict(record) for record in parse_gift_offset_records(data)]


def npc_gift_offset_handler() -> OffsetTableHandler:
    """`npcgiftoffset.dbss` and `npcgiftdataoffset.dbss`, which share one layout."""
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("npc_id", "npcId"),
            offset_column("data_offset", "dataOffset"),
            size_column("data_size", "dataSize"),
        ],
        _read_gift_offsets,
    )


class NpcGiftHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR)["giftColumns"]
        return [
            Column(cols["npcId"], "num", sort_key="npc_id"),
            Column(cols["npcName"], sort_key="npc_name"),
            Column(cols["itemId"], "num", sort_key="item_id"),
            Column(cols["icon"], sort_key="icon_path"),
            Column(cols["itemName"], sort_key="item_name"),
            Column(cols["amity"], "num", sort_key="amity"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return [
            {
                **record,
                "icon_path": icon_path(IconKind.ITEM, record["item_id"]),
                pa_key("item_name"): item_grade_tagged(record["item_name"], item_grade(record["item_id"])),
            }
            for record in parse_npcgift_records(data)
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        loc = is_loc_loaded()

        with_npc_name  = sum(1 for r in records if r["npc_name"])
        with_item_name = sum(1 for r in records if r["item_name"])
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records))
        if loc:
            meta += handler_text(self.lang, _LANG_DIR, "meta.withNpcName", with_npc_name=with_npc_name, with_item_name=with_item_name)

        rows = [
            [
                e(r["npc_id"]),
                e(r["npc_name"] or "-"),
                e(r["item_id"]),
                icon_cell(r["icon_path"]),
                pa_cell(r, "item_name"),
                e(r["amity"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)


class NpcGiftDataHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR)["dataColumns"]
        return [
            Column(cols["npcId"], "num", sort_key="npc_id"),
            Column(cols["npcName"], sort_key="npc_name"),
            Column(cols["dialogue"], sort_key="dialogue"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return [dict(r) for r in parse_npcgiftdata_records(data)]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        loc = is_loc_loaded()

        with_loc = sum(1 for r in records if r["dialogue_source"] == "loc")
        meta = handler_text(self.lang, _LANG_DIR, "meta.dataCount", count=len(records))
        if loc:
            meta += handler_text(self.lang, _LANG_DIR, "meta.withLoc", with_loc=with_loc)

        rows = [
            [
                e(r["npc_id"]),
                e(r["npc_name"] or "-"),
                e(r["dialogue"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
