from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, icon_cell, sort_keys, table
from _common.hunting_ground import hunting_ground_name
from _common.lang import handler_text, load_handler_strings
from _common.loc import loc_text
from _common.offset_table import (
    OffsetColumn,
    OffsetTableHandler,
    offset_column,
    offset_records,
    size_column,
)
from .parser import parse_worldmapmonster_offset_rows, parse_worldmapmonster_records


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "worldmapmonsteroffset.dbss"
_EMPTY = "-"

# Keyed by marker key; str_id4 picks the string.
_LOC_MARKER = 40
_LOC_NAME = 0
_LOC_LINE1 = 1
_LOC_LINE2 = 2

# unknown_kind of the hunting zone markers. Only they point unknown_ref at a
# drop window hunting ground; the Black Shrine markers store 0 to 9 there.
_HUNTING_ZONE_KIND = 0


def _text(key: int, str_id4: int, korean: str) -> str:
    """LOC type 40 text of one marker string, else the stored Korean text."""
    return loc_text(_LOC_MARKER, key, str_id4) or korean.strip()


def _hunting_ground_key(record: dict) -> int | None:
    """The drop window hunting ground of a hunting zone marker, else None."""
    if record["unknown_kind"] != _HUNTING_ZONE_KIND or record["unknown_ref"] < 0:
        return None
    return record["unknown_ref"]


def _hunting_ground_text(key: int | None) -> str:
    """The hunting ground's name, the key where it has none, '' without one."""
    if key is None:
        return ""
    return hunting_ground_name(key) or str(key)


def world_map_monster_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("key", "key", "Key"),
            offset_column("offset", "byteOffset", "Byte Offset"),
            size_column("size", "size", "Size"),
        ],
        offset_records(parse_worldmapmonster_offset_rows, "key"),
    )


class WorldMapMonsterHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("key", "Key"), "num", sort_key="key"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("name", "Name"), sort_key="name"),
            Column(cols.get("label", "Label"), sort_key="label"),
            Column(cols.get("detail", "Detail"), sort_key="detail"),
            Column(cols.get("huntingGround", "Hunting Ground"), sort_key="hunting_ground"),
            Column(cols.get("condition", "Condition"), sort_key="condition"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
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

        records: list[dict] = []
        for record in parse_worldmapmonster_records(data, offset_raw):
            key = record["key"]
            label = _text(key, _LOC_LINE1, record["line1_kr"])
            detail = _text(key, _LOC_LINE2, record["line2_kr"])
            hunting_ground_key = _hunting_ground_key(record)
            records.append({
                **record,
                "name": _text(key, _LOC_NAME, record["name_kr"]),
                "label": label,
                # Many markers repeat the label on the second line.
                "detail": "" if detail == label else detail,
                "hunting_ground_key": hunting_ground_key,
                "hunting_ground": _hunting_ground_text(hunting_ground_key),
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
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records))
        rows = [
            [
                e(r["key"]),
                icon_cell(r["icon_path"]) if r["icon_path"] else _EMPTY,
                e(r["name"] or _EMPTY),
                e(r["label"] or _EMPTY),
                e(r["detail"] or _EMPTY),
                e(r["hunting_ground"] or _EMPTY),
                e(r["condition"] or _EMPTY),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
