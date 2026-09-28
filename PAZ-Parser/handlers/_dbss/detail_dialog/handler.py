from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, join_limited, sort_keys, table, truncate
from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded, loc_lookup, loc_text, strip_pa_tags
from .lease import lease_text
from .parser import DialogRecord, parse_detail_dialog_offset_rows, parse_detail_dialog_records, split_key


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "detail_dialogoffset.dbss"
_LOC_CHARACTER_NAME = 6
# Keyed (dialog key, text_id, 0, field); see the fields below.
_LOC_DIALOG = 39
_FIELD_GREETING = 0
_FIELD_OPTION_TITLE = 2
_EMPTY = "-"
_LIST_PREVIEW_ITEMS = 3
_GREETING_PREVIEW_CHARS = 120


def _greeting_preview(text: str) -> str:
    """The greeting on one line, cut for the table cell."""
    return truncate(" ".join(text.split()), _GREETING_PREVIEW_CHARS)


def _dialog_text(record: DialogRecord, text_id: int, field: int, has_loc: bool) -> str:
    """The user-language text of one dialog string, or "" without LOC."""
    if not has_loc:
        return ""
    return strip_pa_tags(loc_lookup(_LOC_DIALOG, record.key, text_id, 0, field)).strip()


def _record_dict(record: DialogRecord, has_loc: bool) -> dict:
    leases = [option.lease for option in record.options]
    found = [lease for lease in leases if lease is not None]
    return {
        "key": record.key,
        "character_id": record.character_id,
        "dialog_index": record.dialog_index,
        # LOC first; the internal name stands in without it.
        "character": (loc_text(_LOC_CHARACTER_NAME, record.character_id) if has_loc else "")
        or record.internal_name,
        "internal_name": record.internal_name,
        # User language first, the Korean source as fallback.
        "greeting": _dialog_text(record, record.text_id, _FIELD_GREETING, has_loc) or record.greeting,
        "option_count": len(record.options),
        "option_titles": [
            _dialog_text(record, option.text_id, _FIELD_OPTION_TITLE, has_loc) or option.title
            for option in record.options
        ],
        "leases": [lease_text(lease, has_loc) for lease in found],
        "lease_item_ids": [lease.item_id for lease in found],
    }


class DetailDialogOffsetHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("offsetColumns", {})
        return [
            Column(cols.get("characterId", "Character ID"), "num", sort_key="character_id"),
            Column(cols.get("dialog", "Dialog"), "num", sort_key="dialog_index"),
            Column(cols.get("dbssOffset", "DBSS Offset"), "num", sort_key="dbss_offset"),
            Column(cols.get("size", "Size"), "num", sort_key="size"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records = []
        for row in parse_detail_dialog_offset_rows(data):
            character_id, dialog_index = split_key(row.entry_id)
            records.append({
                "key": row.entry_id,
                "character_id": character_id,
                "dialog_index": dialog_index,
                "dbss_offset": row.offset,
                "size": row.size,
            })
        return records

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
            [e(r["character_id"]), e(r["dialog_index"]), e(f"0x{r['dbss_offset']:08X}"), e(r["size"])]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)


class DetailDialogHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("characterId", "Character ID"), "num", sort_key="character_id"),
            Column(cols.get("dialog", "Dialog"), "num", sort_key="dialog_index"),
            Column(cols.get("character", "Character"), sort_key="character"),
            Column(cols.get("greeting", "Greeting"), sort_key="greeting"),
            Column(cols.get("options", "Options"), "num", sort_key="option_count"),
            Column(cols.get("optionTitles", "Option Titles")),
            Column(cols.get("leases", "Leases")),
        ]

    def sortable_fields(self) -> frozenset[str]:
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

        has_loc = is_loc_loaded()
        return [_record_dict(record, has_loc) for record in parse_detail_dialog_records(data, offset_raw)]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        options = sum(r["option_count"] for r in records)
        characters = len({r["character_id"] for r in records})
        meta = f"{len(records):,} dialogs · {characters:,} characters · {options:,} options"
        rows = [
            [
                e(r["character_id"]),
                e(r["dialog_index"]),
                e(r["character"] or _EMPTY),
                e(_greeting_preview(r["greeting"]) or _EMPTY),
                e(r["option_count"]),
                e(join_limited(r["option_titles"], _LIST_PREVIEW_ITEMS) or _EMPTY),
                e(join_limited(r["leases"], _LIST_PREVIEW_ITEMS) or _EMPTY),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
