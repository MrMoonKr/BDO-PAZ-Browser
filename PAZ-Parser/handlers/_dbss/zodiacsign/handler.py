from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, error, sort_keys, table, truncate
from _common.lang import load_handler_strings
from _common.zodiacsign.loc import resolve_loc_type7
from _common.zodiacsign.parser import parse_zodiacsign_records
from .parser import (
    parse_zodiacsignoffset_records,
    parse_zodiacsignorder_records,
    parse_zodiacsignorderoffset_records,
)


_LANG_DIR = Path(__file__).parent / "lang"


_TRAIT_PREVIEW_CHARS = 100


def _truncate(text: str, max_len: int = _TRAIT_PREVIEW_CHARS) -> str:
    return truncate(text, max_len)


class ZodiacSignHandler(PreviewHandler):
    def _columns(self, loc_ok: bool) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        traits_label = (
            cols.get("traitsEn", "Traits (EN)") if loc_ok else cols.get("traitsKr", "Traits (KR)")
        )
        return [
            Column(cols.get("id", "ID"), "num", sort_key="zodiac_id"),
            Column(cols.get("name", "Name"), sort_key="name"),
            Column(cols.get("stars", "Stars"), "num", sort_key="float_count"),
            Column(cols.get("pairs", "Pairs"), "num", sort_key="pairs_count"),
            Column(cols.get("constellation", "Constellation"), sort_key="constellation_name"),
            Column(traits_label, sort_key="trait"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns(loc_ok=True))

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records = parse_zodiacsign_records(data)
        if not records:
            return []

        zodiac_ids = [rec["zodiac_id"] for rec in records]
        loc_names, loc_traits = resolve_loc_type7(zodiac_ids)

        result: list[dict] = []
        for rec in records:
            zid = rec["zodiac_id"]
            result.append({
                "zodiac_id":         zid,
                "name":              loc_names.get(zid, f"#{zid}"),
                "float_count":       rec["float_count"],
                "pairs_count":       rec["pairs_count"],
                "constellation_name": rec["constellation_name"],
                "trait_text":        rec["trait_text"],
                "en_trait":          loc_traits.get(zid, ""),
                "trait":             loc_traits.get(zid) or rec["trait_text"],
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

        loc_ok = any(r["en_trait"] for r in records)

        meta = f"{len(records):,} zodiac signs"
        rows: list[list] = []
        for r in slice_:
            en_trait = r["en_trait"]
            trait_display = (
                _truncate(en_trait) if en_trait else _truncate(r["trait_text"], 60)
            )
            rows.append([
                e(r["zodiac_id"]),
                e(r["name"]),
                e(r["float_count"]),
                e(r["pairs_count"]),
                e(r["constellation_name"]),
                e(trait_display),
            ])

        return table(meta, self._columns(loc_ok), rows)


class ZodiacSignOffsetHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("offsetColumns", {})
        return [
            Column(cols.get("zodiacId", "Zodiac ID"), "num", sort_key="zodiac_id"),
            Column(cols.get("dataOffset", "Data Offset"), "num", sort_key="data_offset"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records = parse_zodiacsignoffset_records(data)
        return [
            {"zodiac_id": rec["zodiac_id"], "data_offset": rec["data_offset"]}
            for rec in records
        ]

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
            [e(r["zodiac_id"]), e(f"0x{r['data_offset']:08X}")]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)


class ZodiacSignOrderHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("orderColumns", {})
        return [
            Column(cols.get("row", "Row"), "num", sort_key="row"),
            Column(cols.get("personality", "Personality"), "num", sort_key="personality_type"),
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

        unique_majors = list({rec["personality_type"] // 100 for rec in records})
        loc_names, _ = resolve_loc_type7(unique_majors)

        result: list[dict] = []
        for rec in records:
            pt = rec["personality_type"]
            major = pt // 100
            variant = pt % 100
            result.append({
                "row":              rec["row"],
                "personality_type": pt,
                "zodiac_name":      loc_names.get(major, f"#{major}"),
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
                e(r["row"]),
                e(r["personality_type"]),
                e(r["zodiac_name"]),
                e(r["variant"]),
                e(r["trigger_count"]),
                e(r["sequence"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)


class ZodiacSignOrderOffsetHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("orderOffsetColumns", {})
        return [
            Column(cols.get("personalityType", "Personality Type"), "num", sort_key="personality_type"),
            Column(cols.get("dataOffset", "Data Offset"), "num", sort_key="data_offset"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records = parse_zodiacsignorderoffset_records(data)
        return [
            {"personality_type": rec["personality_type"], "data_offset": rec["data_offset"]}
            for rec in records
        ]

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
            [e(r["personality_type"]), e(f"0x{r['data_offset']:08X}")]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)

