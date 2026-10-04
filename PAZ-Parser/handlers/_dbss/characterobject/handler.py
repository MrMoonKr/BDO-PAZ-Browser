from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.character import character_name
from _common.loc import is_loc_loaded
from _common.html import Column, e, error, icon_cell, sort_keys, table
from _common.icon_index import IconKind, icon_path
from _common.item_key import item_name_tagged
from _common.lang import load_handler_strings
from _common.lookup_index import IndexKind, lookup
from _common.pabr_offset import parse_pabr_offset_rows
from _common.pa_text import pa_cell, pa_fields
from _common.offset_table import (
    OffsetColumn,
    OffsetTableHandler,
    offset_column,
    offset_records,
    size_column,
)
from .parser import parse_characterobject_records

_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "characterobjectoffset.dbss"
_EMPTY = "-"


def character_object_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("character_id", "characterId", "Character ID"),
            offset_column("offset", "byteOffset", "Byte Offset"),
            size_column("size", "size", "Size"),
        ],
        offset_records(parse_pabr_offset_rows, "character_id"),
    )


class CharacterObjectHandler(PreviewHandler):
    def _columns(self, has_loc: bool) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        columns = [
            Column(cols.get("characterId", "Character ID"), "num", sort_key="character_id"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
        ]
        if has_loc:
            columns.append(Column(cols.get("name", "Name"), sort_key="name"))
        columns.append(Column(cols.get("itemId", "Item ID"), "num", sort_key="item_id"))
        if has_loc:
            columns.append(Column(cols.get("itemName", "Item"), sort_key="item_name"))
        columns += [
            Column(cols.get("objectKind", "Kind"), "num", sort_key="object_kind"),
            Column(cols.get("modelPath", "Model"), sort_key="model_path"),
        ]
        return columns

    def sortable_fields(self) -> tuple[str, ...]:
        # Includes the name, so a saved sort survives LOC not being loaded.
        return sort_keys(self._columns(has_loc=True))

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [
            f"{folder}/{_OFFSET_FILE}",
        ]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get(_OFFSET_FILE)
        if not offset_raw:
            return [{"_error": f"{_OFFSET_FILE} companion not found"}]

        try:
            records = parse_characterobject_records(data, parse_pabr_offset_rows(offset_raw))
        except ValueError as ex:
            return [{"_error": f"characterobject.dbss could not be parsed: {ex}"}]

        has_loc = is_loc_loaded()
        records_out: list[dict] = []
        for r in records:
            item_id = _item_id(r.character_id)
            records_out.append({
                "character_id": r.character_id,
                "icon_path": icon_path(IconKind.CHARACTER, r.character_id),
                "name": character_name(r.character_id),
                "item_id": item_id,
                **pa_fields("item_name", item_name_tagged(item_id) if has_loc and item_id is not None else ""),
                "object_kind": r.object_kind,
                "model_path": r.model_path,
            })
        return records_out

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        if records and "_error" in records[0]:
            return error(records[0]["_error"])

        has_loc = is_loc_loaded()

        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} records"

        rows: list[list[str]] = []
        for r in slice_:
            row: list[str] = [
                e(r["character_id"]),
                icon_cell(r["icon_path"]) if r["icon_path"] else _EMPTY,
            ]
            if has_loc:
                row.append(e(r["name"]))
            row.append(e(r["item_id"] or _EMPTY))
            if has_loc:
                row.append(pa_cell(r, "item_name"))
            row.append(e(r["object_kind"]))
            row.append(e(r["model_path"]))
            rows.append(row)

        return table(meta, self._columns(has_loc), rows)


def _item_id(character_id: int) -> int | None:
    """The one item that places or summons the character, or None.

    None also covers characters named by several items and a missing index.
    """
    item_id = lookup(IndexKind.CHARACTER_ITEM, character_id)
    return item_id if isinstance(item_id, int) else None
