from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.buff import buff_label, buff_list_cell
from _common.html import Column, e, icon_cell, sort_keys, table
from _common.item_grade import item_grade_tagged
from _common.lang import load_handler_strings
from _common.loc import LOC_NULL, loc_tagged, loc_text
from _common.pa_text import pa_cell, pa_fields, pa_line_cell
from _common.skill import skill_buff_ids
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, size_column
from .parser import (
    parse_itemenchant_records,
    parse_itemenchantoffset_records,
)


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "itemenchantoffset.dbss"

# Item names are LOC type 0 keyed by item ID; character names type 6.
_LOC_TYPE_ITEM = 0
# LOC type 0 field of the item description.
_LOC_ITEM_DESCRIPTION = 1
_LOC_TYPE_CHARACTER = 6

_EMPTY = "-"
_LIST_PREVIEW_ITEMS = 3


def _item_description_tagged(item_id: int) -> str:
    """The item's LOC description with its PA tags, or ''; the file stores none of its own."""
    text = loc_tagged(_LOC_TYPE_ITEM, item_id, _LOC_ITEM_DESCRIPTION)
    return "" if text == LOC_NULL else text


def _item_name(record: dict) -> str:
    return loc_text(_LOC_TYPE_ITEM, record["item_id"]) or record["name_kr"]


def _with_links(record: dict) -> dict:
    """The parsed record plus its item name, placed character and buffs."""
    buff_ids = skill_buff_ids(record["skill_keys"])
    return {
        **record,
        # In its grade colour, as the game draws item names; Korean when LOC has no row.
        **pa_fields("item_name", item_grade_tagged(_item_name(record), record["grade"])),
        **pa_fields("description", _item_description_tagged(record["item_id"])),
        # 0 means "places no character"; None sorts last and exports empty.
        "character_id": record["character_id"] or None,
        "character_name": (
            loc_text(_LOC_TYPE_CHARACTER, record["character_id"])
            if record["character_id"]
            else ""
        ),
        # Both skills' buffs, in slot order, from the SKILL_BUFFS lookup index.
        "buff_ids": buff_ids,
        "buffs": [buff_label(buff_id) for buff_id in buff_ids],
        "buff_count": len(buff_ids) or None,
    }


def item_enchant_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("item_id", "itemId", "Item ID"),
            OffsetColumn("enchant_level", "enchantLevel", "Enchant Level"),
            offset_column("data_offset", "dataOffset", "Data Offset"),
            size_column("data_size", "dataSize", "Data Size"),
        ],
        parse_itemenchantoffset_records,
    )


class ItemEnchantHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("itemId", "Item ID"), "num", sort_key="item_id"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("item", "Item"), sort_key="item_name"),
            Column(cols.get("description", "Description"), sort_key="description"),
            Column(cols.get("maxLevel", "Max Level"), "num", sort_key="max_enchant_level"),
            Column(cols.get("objectId", "Object ID"), "num", sort_key="character_id"),
            Column(cols.get("object", "Object"), sort_key="character_name"),
            Column(cols.get("buffs", "Buffs"), sort_key="buff_count"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
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

        return [_with_links(record) for record in parse_itemenchant_records(data, offset_raw)]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        enhanceable = sum(1 for record in records if record["max_enchant_level"])
        meta = f"{len(records):,} items · {enhanceable:,} enhanceable"

        with_icon = sum(1 for record in records if record["icon_path"])
        if with_icon:
            meta += f" · {with_icon:,} icon paths"

        rows = [
            [
                e(record["item_id"]),
                icon_cell(record["icon_path"]) if record["icon_path"] else _EMPTY,
                pa_cell(record, "item_name") if record["item_name"] else e(record["item_id"]),
                pa_line_cell(record, "description"),
                e(record["max_enchant_level"]),
                e(record["character_id"]) if record["character_id"] is not None else _EMPTY,
                e(record["character_name"] or _EMPTY),
                buff_list_cell(record["buff_ids"], _LIST_PREVIEW_ITEMS) or _EMPTY,
            ]
            for record in slice_
        ]
        return table(meta, self._columns(), rows)
