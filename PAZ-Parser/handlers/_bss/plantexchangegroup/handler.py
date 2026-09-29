from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, join_limited, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded
from _common.production_items import production_item_fields
from _bwp.waypoint.worldmap import worldmap_companion, worldmap_links
from _dbss.plantzone.parser import parse_plantzone_records
from .node_names import english_group_names
from .parser import parse_plantexchangegroup_records


_LANG_DIR = Path(__file__).parent / "lang"
_ZONE_FILE = "plantzone.dbss"
_ZONE_OFFSET_FILE = "plantzoneoffset.dbss"
_EMPTY = "-"
_LIST_PREVIEW_ITEMS = 8


def _english_names(companions: dict[str, bytes]) -> dict[int, str]:
    """English group names by production key; empty without LOC or the node tables."""
    zones = companions.get(_ZONE_FILE)
    zone_offsets = companions.get(_ZONE_OFFSET_FILE)
    if not is_loc_loaded() or zones is None or zone_offsets is None:
        return {}
    # Without the worldmap no zone has a parent, so no key gets a name.
    return english_group_names(parse_plantzone_records(zones, zone_offsets), worldmap_links(companions))


class PlantExchangeGroupBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("productionKey", "Production Key"), "num", sort_key="production_key"),
            Column(cols.get("name", "Name"), sort_key="name"),
            Column(cols.get("itemSubgroup", "Item Subgroup"), "num", sort_key="item_subgroup_key"),
            # A list column: it would only sort by its string form.
            Column(cols.get("items", "Items")),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [
            f"{folder}/{_ZONE_FILE}",
            f"{folder}/{_ZONE_OFFSET_FILE}",
            worldmap_companion(entry),
        ]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        english = _english_names(companions)
        records: list[dict] = []
        for record in parse_plantexchangegroup_records(data):
            name_en = english.get(record["production_key"], "")
            records.append({
                **record,
                **production_item_fields(record["production_key"]),
                "name_en": name_en,
                # The Korean label stands in where no English name is unique.
                "name": name_en or record["name_kr"],
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
        resolved = sum(1 for record in records if record["item_keys"] is not None)
        meta = f"{len(records):,} production groups · {resolved:,} with items"
        rows = [
            [
                e(record["production_key"]),
                e(record["name"] or _EMPTY),
                e(record["item_subgroup_key"]),
                e(join_limited(record["items"], _LIST_PREVIEW_ITEMS) or _EMPTY),
            ]
            for record in slice_
        ]
        return table(meta, self._columns(), rows)
