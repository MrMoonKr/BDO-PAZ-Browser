from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, error, sort_keys, table
from _common.lang import load_handler_strings
from .parser import (
    parse_mentalcard_offset_records,
    parse_mentalcard_records,
)


_LANG_DIR = Path(__file__).parent / "lang"


class MentalCardOffsetHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("offsetColumns", {})
        return [
            Column(cols.get("internalId", "Internal ID"), "num", sort_key="internal_id"),
            Column(cols.get("dbssOffset", "DBSS Offset"), "num", sort_key="dbss_offset"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records = parse_mentalcard_offset_records(data)
        return [
            {"internal_id": internal_id, "dbss_offset": dbss_offset}
            for row, dbss_offset, size, internal_id in records
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
            [e(r["internal_id"]), e(f"0x{r['dbss_offset']:08X}")]
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
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/mentalcardoffset.dbss"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get("mentalcardoffset.dbss")
        if offset_raw is None:
            raise ValueError("mentalcardoffset.dbss companion not found.")

        records = parse_mentalcard_records(data, offset_raw)
        return [
            {
                "entry_id":   record["entry_id"],
                "entry_name": record["entry_name"] or "",
                "node_id":    record["node_id"],
                "node_name":  record["node_name"] or "",
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

        with_entry_name = sum(1 for r in records if r["entry_name"])
        with_node_name  = sum(1 for r in records if r["node_name"])
        meta = (
            f"{len(records):,} mentalcard records"
            f" · {with_entry_name:,} entry names · {with_node_name:,} node names"
        )

        rows = [
            [
                e(r["entry_id"]),
                e(r["entry_name"] or "-"),
                e(r["node_id"]),
                e(r["node_name"] or "-"),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
