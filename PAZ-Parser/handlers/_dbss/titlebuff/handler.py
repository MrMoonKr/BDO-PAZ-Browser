from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.binary import parse_offset_table
from _common.html import Column, e, sort_keys, table
from _common.lang import handler_text, load_handler_strings
from _common.pa_text import pa_cell, pa_fields
from _common.offset_table import (
    OffsetColumn,
    OffsetTableHandler,
    offset_column,
    offset_map_records,
)
from _bss.stringtable.parser import GAME_SHEET
from _bss.stringtable.text import STRINGTABLE_FILE, ui_key_hashes, ui_key_tagged
from .model import TitleBuffRecord
from .parser import parse_titlebuff_records


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "titlebufflistoffset.dbss"
# The Title Effects tooltip: one line per tier, in tier order.
_TOOLTIP_KEY = "LUA_CHARACTERINFO_TITLE_TOOLTIP_DESC"


def _tooltip_lines(stringtable: bytes | None, tier_count: int) -> list[str]:
    """The tooltip lines in the user language with their PA tags, or [] when
    LOC or `stringtable.bss` is missing or the line count does not match."""
    hashes = ui_key_hashes(stringtable, [GAME_SHEET])
    lines = [line.strip() for line in ui_key_tagged(hashes, GAME_SHEET, _TOOLTIP_KEY).splitlines()]
    return lines if len(lines) == tier_count else []


def _tier_text(record: TitleBuffRecord, lines: list[str]) -> str:
    """The tier's tooltip line, else its inline Korean label and effects."""
    return lines[record["tier_id"]] if lines else record["label_kr"] + record["effect_kr"]


def title_buff_list_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("buff_id", "buffId", "Buff ID"),
            offset_column("offset", "offset", "Offset"),
        ],
        offset_map_records("buff_id"),
    )


class TitleBuffListHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("level", "Level"), "num", sort_key="level"),
            Column(cols.get("requiredTitles", "Required Titles"), "num", sort_key="required_titles"),
            Column(cols.get("text", "Text"), sort_key="text"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/{_OFFSET_FILE}", f"{folder}/{STRINGTABLE_FILE}"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get(_OFFSET_FILE)
        if offset_raw is None:
            raise ValueError(f"{_OFFSET_FILE} companion not found, cannot parse blocks.")

        records = parse_titlebuff_records(data, parse_offset_table(offset_raw))
        # User language first; the inline Korean stands in without LOC.
        lines = _tooltip_lines(companions.get(STRINGTABLE_FILE), len(records))
        return [
            {
                **record,
                "level": record["tier_id"] + 1,
                **pa_fields("text", _tier_text(record, lines)),
            }
            for record in records
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]

        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records))
        rows = [
            [e(r["level"]), e(r["required_titles"]), pa_cell(r, "text")]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
