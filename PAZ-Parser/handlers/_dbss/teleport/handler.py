from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _bwp.waypoint.worldmap import worldmap_companion, worldmap_waypoints
from _common.html import Column, e, sort_keys, table
from _common.lang import handler_text, load_handler_strings
from _common.node import full_node_name
from _common.pa_text import pa_key
from _common.teleport import teleport_buff_ids
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, size_column
from .nearest import named_nodes, nearest_node
from .parser import parse_teleport_offset_rows, parse_teleport_records
from .used_by import used_by_cell, used_by_entries


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"
_LIST_PREVIEW_ITEMS = 3


def teleport_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("index", "index"),
            OffsetColumn("section", "section"),
            offset_column("offset", "byteOffset"),
            size_column("size", "size"),
        ],
        parse_teleport_offset_rows,
    )


class TeleportHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR)["columns"]
        return [
            Column(cols["key"], "num", sort_key="key"),
            Column(cols["section"], "num", sort_key="section"),
            Column(cols["x"], "num", sort_key="x"),
            Column(cols["y"], "num", sort_key="y"),
            Column(cols["z"], "num", sort_key="z"),
            Column(cols["nearestNode"], sort_key="nearest_node"),
            Column(cols["distance"], "num", sort_key="distance_m"),
            Column(cols["usedBy"], sort_key="used_by_count"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        return [worldmap_companion(entry)]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        nodes = named_nodes(worldmap_waypoints(companions), full_node_name)
        records: list[dict] = []
        for record in parse_teleport_records(data):
            nearest = nearest_node(record["x"], record["z"], nodes)
            buff_ids = teleport_buff_ids(record["section"], record["key"])
            entries = used_by_entries(buff_ids)
            records.append({
                **record,
                # None without the worldmap graph, so the columns sort last.
                "nearest_node_key": nearest.key if nearest else None,
                "nearest_node": nearest.name if nearest else None,
                "distance_m": round(nearest.distance_m) if nearest else None,
                "used_by_buff_ids": list(buff_ids),
                "used_by_icons": [entry.icon_path for entry in entries],
                "used_by": [entry.label for entry in entries],
                pa_key("used_by"): [entry.tagged_label for entry in entries],
                "used_by_tooltips": [entry.tooltip for entry in entries],
                "used_by_count": len(entries) or None,
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
                e(r["section"]),
                e(f"{r['x']:,.0f}"),
                e(f"{r['y']:,.0f}"),
                e(f"{r['z']:,.0f}"),
                e(r["nearest_node"] or _EMPTY),
                e(_EMPTY if r["distance_m"] is None else f"{r['distance_m']:,}"),
                used_by_cell(r["used_by_icons"], r[pa_key("used_by")], r["used_by_tooltips"], _LIST_PREVIEW_ITEMS)
                or _EMPTY,
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
