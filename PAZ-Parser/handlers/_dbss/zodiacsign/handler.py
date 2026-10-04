from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table, truncate
from _common.lang import load_handler_strings
from _common.zodiacsign.loc import zodiac_name, zodiac_trait
from _common.zodiacsign.parser import parse_zodiacsign_records
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, picked_records
from .parser import (
    parse_zodiacsignoffset_records,
    parse_zodiacsignorder_records,
    parse_zodiacsignorderoffset_records,
)


_LANG_DIR = Path(__file__).parent / "lang"


_TRAIT_PREVIEW_CHARS = 100


class ZodiacSignHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("id", "ID"), "num", sort_key="zodiac_id"),
            Column(cols.get("name", "Name"), sort_key="name"),
            Column(cols.get("stars", "Stars"), "num", sort_key="float_count"),
            Column(cols.get("pairs", "Pairs"), "num", sort_key="pairs_count"),
            Column(cols.get("traits", "Traits"), sort_key="trait"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        # User language first; the inline Korean name and traits stand in without LOC.
        return [
            {
                "zodiac_id": rec["zodiac_id"],
                "name": zodiac_name(rec["zodiac_id"], rec["constellation_name"]),
                "float_count": rec["float_count"],
                "pairs_count": rec["pairs_count"],
                "constellation_name": rec["constellation_name"],
                "trait_text": rec["trait_text"],
                "trait": zodiac_trait(rec["zodiac_id"], rec["trait_text"]),
            }
            for rec in parse_zodiacsign_records(data)
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]

        meta = f"{len(records):,} zodiac signs"
        rows = [
            [
                e(r["zodiac_id"]),
                e(r["name"]),
                e(r["float_count"]),
                e(r["pairs_count"]),
                e(truncate(r["trait"], _TRAIT_PREVIEW_CHARS)),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)


def zodiac_sign_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("zodiac_id", "zodiacId", "Zodiac ID"),
            offset_column("data_offset", "dataOffset", "Data Offset"),
        ],
        picked_records(parse_zodiacsignoffset_records, ("zodiac_id", "data_offset")),
    )


class ZodiacSignOrderHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("orderColumns", {})
        return [
            Column(cols.get("personality", "Personality"), "num", sort_key="personality_type"),
            Column(cols.get("row", "Row"), "num", sort_key="row"),
            Column(cols.get("zodiac", "Zodiac"), sort_key="zodiac_name"),
            Column(cols.get("variant", "Variant"), "num", sort_key="variant"),
            Column(cols.get("triggers", "Triggers"), "num", sort_key="trigger_count"),
            Column(cols.get("sequence", "Sequence"), sort_key="sequence"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/zodiacsignorderoffset.dbss"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get("zodiacsignorderoffset.dbss")
        if offset_raw is None:
            raise ValueError("zodiacsignorderoffset.dbss companion not found.")

        records = parse_zodiacsignorder_records(data, offset_raw)
        if not records:
            return []

        result: list[dict] = []
        for rec in records:
            pt = rec["personality_type"]
            major = pt // 100
            variant = pt % 100
            result.append({
                "row":              rec["row"],
                "personality_type": pt,
                "zodiac_name":      zodiac_name(major),
                "variant":          variant,
                "trigger_count":    rec["trigger_count"],
                "trigger_order":    rec["trigger_order"],
                "sequence":         "→".join(str(s) for s in rec["trigger_order"]),
            })

        return result

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} order records"
        rows = [
            [
                e(r["personality_type"]),
                e(r["row"]),
                e(r["zodiac_name"]),
                e(r["variant"]),
                e(r["trigger_count"]),
                e(r["sequence"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)


def zodiac_sign_order_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("personality_type", "personalityType", "Personality Type"),
            offset_column("data_offset", "dataOffset", "Data Offset"),
        ],
        picked_records(parse_zodiacsignorderoffset_records, ("personality_type", "data_offset")),
        lang_block="orderOffsetColumns",
    )
