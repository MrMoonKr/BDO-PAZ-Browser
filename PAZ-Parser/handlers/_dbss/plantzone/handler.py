from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, join_limited, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import loc_text
from _common.production_items import production_item_fields
from .parser import WORKER_SPECIES_NAMES, parse_offset_records, parse_plantzone_records


_LANG_DIR = Path(__file__).parent / "lang"
_LOC_NODE_NAME = 29
_EMPTY = "-"
_LIST_PREVIEW_ITEMS = 8


def _species_name(species: int) -> str:
    return WORKER_SPECIES_NAMES[species] if species < len(WORKER_SPECIES_NAMES) else str(species)


class PlantZoneOffsetHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("offsetColumns", {})
        return [
            Column(cols.get("recordId", "Record ID"), "num", sort_key="record_id"),
            Column(cols.get("dataOffset", "Data Offset"), "num", sort_key="data_offset"),
            Column(cols.get("dataSize", "Data Size"), "num", sort_key="data_size"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return parse_offset_records(data)

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
            [
                e(r["record_id"]),
                e(f"0x{r['data_offset']:08X}"),
                e(r["data_size"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)


class PlantZoneHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("zoneId", "Zone ID"), "num", sort_key="record_id"),
            Column(cols.get("nodeName", "Node Name"), sort_key="node_name"),
            Column(cols.get("productionKey", "Production Key"), "num", sort_key="production_key"),
            # A list column: it would only sort by its string form.
            Column(cols.get("producedItems", "Produced Items")),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/plantzoneoffset.dbss"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get("plantzoneoffset.dbss")
        if offset_raw is None:
            raise ValueError("plantzoneoffset.dbss companion not found.")

        return [
            {
                **record,
                **production_item_fields(record["production_key"]),
                "node_name": loc_text(_LOC_NODE_NAME, record["record_id"]),
                # Not shown: the list is not a worker lock and its use is
                # unknown. Kept for search and export.
                "worker_species_text": ", ".join(
                    _species_name(species) for species in record["worker_species"]
                ),
            }
            for record in parse_plantzone_records(data, offset_raw)
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        resolved = sum(1 for record in records if record["item_keys"] is not None)
        meta = f"{len(records):,} plant zone records · {resolved:,} with items"
        rows = [
            [
                e(r["record_id"]),
                e(r["node_name"] or _EMPTY),
                e(r["production_key"]),
                e(join_limited(r["items"], _LIST_PREVIEW_ITEMS) or _EMPTY),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
