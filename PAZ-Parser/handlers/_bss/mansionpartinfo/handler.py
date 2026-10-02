from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.character import character_name
from _common.html import Column, e, icon_cell, sort_keys, table
from _common.lang import load_handler_strings
from .parser import parse_mansionpartinfo_records


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"


class MansionPartInfoBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("manorId", "Manor ID"), "num", sort_key="character_id"),
            Column(cols.get("manor", "Manor"), sort_key="manor"),
            Column(cols.get("part", "Part"), "num", sort_key="part_index"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        # The file holds no text, so without LOC the manor name is empty.
        return [
            {**record, "manor": character_name(record["character_id"])}
            for record in parse_mansionpartinfo_records(data)
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} manor parts"
        rows = [
            [
                e(r["character_id"]),
                e(r["manor"] or _EMPTY),
                e(r["part_index"]),
                icon_cell(r["icon_path"]) if r["icon_path"] else _EMPTY,
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
