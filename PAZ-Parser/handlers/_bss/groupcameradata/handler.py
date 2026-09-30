from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, icon_cell, sort_keys, table, truncate
from _common.lang import load_handler_strings
from _common.loc import loc_text
from .parser import parse_groupcameradata_records


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"
_DESCRIPTION_PREVIEW_CHARS = 120

# Keyed by scene ID; str_id4 picks the string.
_LOC_CUTSCENE = 97
_LOC_TITLE = 0
_LOC_DESCRIPTION = 1
_LOC_QUOTE = 2


def _text(scene_id: int, str_id4: int, korean: str) -> str:
    """LOC type 97 text of one scene string, else the stored Korean text."""
    return loc_text(_LOC_CUTSCENE, scene_id, str_id4) or korean.strip()


class GroupCameraDataBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("sceneId", "Scene ID"), "num", sort_key="scene_id"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("title", "Title"), sort_key="title"),
            Column(cols.get("description", "Description"), sort_key="description"),
            Column(cols.get("quote", "Quote"), sort_key="quote"),
        ]

    def sortable_fields(self) -> frozenset[str]:
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
                "title": _text(record["scene_id"], _LOC_TITLE, record["title_kr"]),
                "description": _text(record["scene_id"], _LOC_DESCRIPTION, record["description_kr"]),
                "quote": _text(record["scene_id"], _LOC_QUOTE, record["quote_kr"]),
            }
            for record in parse_groupcameradata_records(data)
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} cutscenes"
        rows = [
            [
                e(r["scene_id"]),
                icon_cell(r["icon_path"]) if r["icon_path"] else _EMPTY,
                e(r["title"] or _EMPTY),
                e(truncate(" ".join(r["description"].split()), _DESCRIPTION_PREVIEW_CHARS) or _EMPTY),
                e(r["quote"] or _EMPTY),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
