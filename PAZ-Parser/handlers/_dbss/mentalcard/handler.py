from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags
from .parser import parse_mentalcard_offset_records, parse_mentalcard_records


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "mentalcardoffset.dbss"
_LOC_THEME = 9
_LOC_KNOWLEDGE = 34
_EMPTY = "-"


def _loc_text(str_type: int, key: int) -> str:
    return strip_pa_tags(loc_lookup(str_type, key) or "").strip()


class MentalCardOffsetHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("offsetColumns", {})
        return [
            Column(cols.get("cardId", "Knowledge ID"), "num", sort_key="card_id"),
            Column(cols.get("dbssOffset", "DBSS Offset"), "num", sort_key="dbss_offset"),
            Column(cols.get("size", "Size"), "num", sort_key="size"),
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
            {"card_id": row.card_id, "dbss_offset": row.offset, "size": row.size}
            for row in parse_mentalcard_offset_records(data)
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
            [e(r["card_id"]), e(f"0x{r['dbss_offset']:08X}"), e(r["size"])]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)


class MentalCardHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("knowledgeId", "Knowledge ID"), "num", sort_key="entry_id"),
            Column(cols.get("knowledgeName", "Knowledge Name"), sort_key="entry_name"),
            Column(cols.get("categoryId", "Category ID"), "num", sort_key="node_id"),
            Column(cols.get("categoryName", "Category Name"), sort_key="node_name"),
            Column(cols.get("minFavor", "Min Favor"), "num", sort_key="min_favor"),
            Column(cols.get("maxFavor", "Max Favor"), "num", sort_key="max_favor"),
            Column(cols.get("interest", "Interest"), "num", sort_key="interest"),
        ]

    def sortable_fields(self) -> frozenset[str]:
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

        has_loc = is_loc_loaded()
        return [
            {
                "entry_id": record.card_id,
                # LOC first; the Korean source name stands in without it.
                "entry_name": (_loc_text(_LOC_KNOWLEDGE, record.card_id) if has_loc else "")
                or record.name_kr,
                "node_id": record.theme_id,
                "node_name": _loc_text(_LOC_THEME, record.theme_id) if has_loc else "",
                # Stored as floats but always whole numbers.
                "min_favor": round(record.min_favor),
                "max_favor": round(record.max_favor),
                "interest": round(record.interest),
            }
            for record in parse_mentalcard_records(data, offset_raw)
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]

        with_node_name = sum(1 for r in records if r["node_name"])
        meta = f"{len(records):,} knowledge cards · {with_node_name:,} category names"

        rows = [
            [
                e(r["entry_id"]),
                e(r["entry_name"] or _EMPTY),
                e(r["node_id"]),
                e(r["node_name"] or _EMPTY),
                e(r["min_favor"]),
                e(r["max_favor"]),
                e(r["interest"]),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
