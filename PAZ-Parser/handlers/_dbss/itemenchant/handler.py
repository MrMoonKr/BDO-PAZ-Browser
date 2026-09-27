from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, icon_cell, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags
from .parser import (
    parse_itemenchant_records,
    parse_itemenchantoffset_records,
)


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "itemenchantoffset.dbss"

# Item display names live in LOC type 0, keyed by item ID.
_LOC_TYPE_ITEM = 0

_EMPTY = "-"


def _item_name(item_id: int) -> str:
    if not is_loc_loaded():
        return ""

    return strip_pa_tags(loc_lookup(_LOC_TYPE_ITEM, item_id, 0, 0, 0)).strip()


class ItemEnchantOffsetHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("offsetColumns", {})
        return [
            Column(cols.get("itemId", "Item ID"), "num", sort_key="item_id"),
            Column(cols.get("dataOffset", "Data Offset"), "num", sort_key="data_offset"),
            Column(cols.get("dataSize", "Data Size"), "num", sort_key="data_size"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return parse_itemenchantoffset_records(data)

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} offset records"
        rows = [
            [
                e(record["item_id"]),
                e(f"0x{record['data_offset']:08X}"),
                e(f"{record['data_size']:,}"),
            ]
            for record in slice_
        ]
        return table(meta, self._columns(), rows)


class ItemEnchantHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("itemId", "Item ID"), "num", sort_key="item_id"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("item", "Item"), sort_key="item_name"),
            Column(cols.get("characterId", "Character ID"), "num", sort_key="character_id"),
            Column(cols.get("effectTag", "Effect Tag"), sort_key="effect_tag"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        if folder == entry.internal_path:
            return [_OFFSET_FILE]
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
                **record,
                "item_name": _item_name(record["item_id"]),
                # 0 means "places no character"; None sorts last and exports empty.
                "character_id": record["character_id"] or None,
            }
            for record in parse_itemenchant_records(data, offset_raw)
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        items = len({record["item_id"] for record in records})
        meta = f"{len(records):,} records across {items:,} items"

        with_icon = sum(1 for record in records if record["icon_path"])
        if with_icon:
            meta += f" · {with_icon:,} icon paths"

        rows = [
            [
                e(record["item_id"]),
                icon_cell(record["icon_path"]) if record["icon_path"] else _EMPTY,
                e(record.get("item_name") or record["item_id"]),
                e(record["character_id"]) if record["character_id"] is not None else _EMPTY,
                e(record["effect_tag"] or _EMPTY),
            ]
            for record in slice_
        ]
        return table(meta, self._columns(), rows)
