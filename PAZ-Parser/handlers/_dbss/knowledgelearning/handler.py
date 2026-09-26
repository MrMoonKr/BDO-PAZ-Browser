from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings
from .parser import (
    parse_knowledgelearning_offset_records,
    parse_knowledgelearning_records,
)


_LANG_DIR = Path(__file__).parent / "lang"


class KnowledgeLearningOffsetHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("offsetColumns", {})
        return [
            Column(cols.get("idxId", "Idx ID"), "num", sort_key="idx_id"),
            Column(cols.get("kind", "Kind"), "num", sort_key="kind"),
            Column(cols.get("dbssOffset", "DBSS Offset"), "num", sort_key="offset"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records = parse_knowledgelearning_offset_records(data)
        return [
            {"idx_id": rec["idx_id"], "kind": rec["kind"], "offset": rec["offset"]}
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
            [e(r["idx_id"]), e(r["kind"]), e(f"0x{r['offset']:08X}")]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)


class KnowledgeLearningHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("knowledgeId", "Knowledge ID"), "num", sort_key="knowledge_id"),
            Column(cols.get("kind", "Kind"), "num", sort_key="kind"),
            Column(cols.get("knowledgeName", "Knowledge Name"), sort_key="knowledge_name"),
            Column(cols.get("offset", "Offset"), "num", sort_key="offset"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/knowledgelearningoffset.dbss"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get("knowledgelearningoffset.dbss")
        if offset_raw is None:
            raise ValueError("knowledgelearningoffset.dbss companion not found.")

        records = parse_knowledgelearning_records(data, offset_raw)
        return [
            {
                "knowledge_id":   record["knowledge_id"] or "",
                "kind":           record["kind"],
                "knowledge_name": record["knowledge_name"] or "",
                "offset":         record["offset"],
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

        with_knowledge_name = sum(1 for r in records if r["knowledge_name"])
        meta = (
            f"{len(records):,} records"
            f" · {with_knowledge_name:,} knowledge names"
        )

        rows = [
            [
                e(r["knowledge_id"] or "-"),
                e(r["kind"]),
                e(r["knowledge_name"] or "-"),
                e(f"0x{r['offset']:08X}"),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
