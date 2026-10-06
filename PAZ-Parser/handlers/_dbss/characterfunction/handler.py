from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.character import character_name
from _common.html import Column, e, error, sort_keys, table, text_list_cell
from _common.lang import handler_text, load_handler_strings
from _common.loc import is_loc_loaded
from _common.offset_table import (
    OffsetColumn,
    OffsetTableHandler,
    offset_column,
    offset_records,
    size_column,
)
from _common.pabr_offset import parse_pabr_offset_rows
from .parser import CharacterFunctionRecord, parse_characterfunction_records
from .text import function_labels, node_names

_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "characterfunctionoffset.dbss"
_EMPTY = "-"
_LIST_PREVIEW_ITEMS = 6


def character_function_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("character_id", "characterId"),
            offset_column("offset", "byteOffset"),
            size_column("size", "size"),
        ],
        offset_records(parse_pabr_offset_rows, "character_id"),
    )


class CharacterFunctionHandler(PreviewHandler):
    def _columns(self, has_loc: bool) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR)["columns"]
        columns = [Column(cols["characterId"], "num", sort_key="character_id")]
        if has_loc:
            columns.append(Column(cols["name"], sort_key="name"))
        columns += [
            Column(cols["functions"], sort_key="functions_text"),
            Column(cols["managedNodes"], sort_key="managed_nodes_text"),
            Column(cols["town"], sort_key="town_nodes_text"),
        ]
        return columns

    def sortable_fields(self) -> tuple[str, ...]:
        # Includes the name, so a saved sort survives LOC not being loaded.
        return sort_keys(self._columns(has_loc=True))

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
        if not offset_raw:
            return [{"_error": f"{_OFFSET_FILE} companion not found"}]

        try:
            records = parse_characterfunction_records(data, parse_pabr_offset_rows(offset_raw))
        except ValueError as ex:
            return [{"_error": f"characterfunction.dbss could not be parsed: {ex}"}]

        return [_record_fields(record) for record in records]

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
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records))

        rows: list[list[str]] = []
        for r in records[start : start + page_size]:
            row = [e(r["character_id"])]
            if has_loc:
                row.append(e(r["name"] or _EMPTY))
            row += [
                text_list_cell(r["functions"], _LIST_PREVIEW_ITEMS) or _EMPTY,
                text_list_cell(r["managed_nodes"], _LIST_PREVIEW_ITEMS) or _EMPTY,
                text_list_cell(r["town_nodes"], _LIST_PREVIEW_ITEMS) or _EMPTY,
            ]
            rows.append(row)

        return table(meta, self._columns(has_loc), rows)


def _record_fields(record: CharacterFunctionRecord) -> dict:
    functions = function_labels(record)
    managed_nodes = node_names(record.managed_node_keys)
    town_nodes = node_names(record.town_node_keys)
    return {
        "character_id": record.character_id,
        "name": character_name(record.character_id),
        "functions": functions,
        # Full lists as text, so tab search, sorting and CSV export see every entry.
        "functions_text": ", ".join(functions),
        "managed_node_keys": list(record.managed_node_keys),
        "managed_nodes": managed_nodes,
        "managed_nodes_text": ", ".join(managed_nodes),
        "town_node_keys": list(record.town_node_keys),
        "town_nodes": town_nodes,
        "town_nodes_text": ", ".join(town_nodes),
    }
