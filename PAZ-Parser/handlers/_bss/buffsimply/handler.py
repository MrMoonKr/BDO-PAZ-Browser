from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.buff import buff_loc_description
from _common.html import Column, e, icon_cell, sort_keys, table
from _common.lang import handler_text, load_handler_strings
from _common.pa_text import pa_cell, pa_fields
from .parser import parse_buffsimply_records


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"


class BuffSimplyBssHandler(PreviewHandler):
    def _strings(self) -> dict:
        return load_handler_strings(self.lang, _LANG_DIR)

    def _columns(self) -> list[Column]:
        cols = self._strings()["columns"]
        return [
            Column(cols["buffId"], "num", sort_key="buff_id"),
            Column(cols["icon"], sort_key="icon_path"),
            Column(cols["description"], sort_key="description"),
            Column(cols["shown"], sort_key="is_shown"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        # The file holds no inline text, so without LOC the description is empty.
        return [
            {**record, **pa_fields("description", buff_loc_description(record["buff_id"]))}
            for record in parse_buffsimply_records(data)
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        values = self._strings()["values"]
        yes, no = values["yes"], values["no"]
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records))
        rows = [
            [
                e(r["buff_id"]),
                icon_cell(r["icon_path"]) if r["icon_path"] else _EMPTY,
                pa_cell(r, "description"),
                e(yes if r["is_shown"] else no),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
