from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, icon_cell, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import loc_text
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, size_column
from .parser import parse_petaction_records, parse_petactionoffset_records


_LANG_DIR = Path(__file__).parent / "lang"
_LOC_PET_ACTION = 19


def _with_action_name(record: dict) -> dict:
    """The record named in the user language, else Korean, else its icon suffix.

    The Korean name is the real one; the icon suffix is only a guess ("Like"
    for Joy), so it is the last resort.
    """
    icon_action_name = record["action_name"]
    loc_name = loc_text(_LOC_PET_ACTION, record["action_id"])
    return {
        **record,
        "icon_action_name": icon_action_name,
        "has_loc_name": bool(loc_name),
        "action_name": loc_name or record["name_kr"] or icon_action_name,
    }


def pet_action_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("action_id", "actionId", "Action ID"),
            offset_column("record_offset", "recordOffset", "Record Offset"),
            size_column("record_size", "recordSize", "Record Size"),
        ],
        parse_petactionoffset_records,
    )


class PetActionHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("actionId", "Action ID"), "num", sort_key="action_id"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("actionName", "Action Name"), sort_key="action_name"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [
            f"{folder}/petactionoffset.dbss",
        ]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get("petactionoffset.dbss")
        if offset_raw is None:
            raise ValueError("petactionoffset.dbss companion not found.")
        return [_with_action_name(record) for record in parse_petaction_records(data, offset_raw)]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} pet actions"
        with_loc = sum(1 for r in records if r["has_loc_name"])
        if with_loc:
            meta += f" · {with_loc:,} with LOC type 19 names"
        rows = [
            [
                e(r["action_id"]),
                icon_cell(r["icon_path"]),
                e(r["action_name"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
