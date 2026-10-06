from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.character import LOC_CHARACTER_NAME
from _common.html import Column, e, sort_keys, table
from _common.item_key import LOC_ITEM_NAME
from _common.knowledge import knowledge_name
from _common.lang import handler_text, load_handler_strings
from _common.loc import is_loc_loaded, loc_text
from _common.offset_table import OffsetColumn, OffsetTableHandler, offset_column, size_column
from .parser import (
    SOURCE_ITEM,
    parse_knowledgelearning_offset_records,
    parse_knowledgelearning_records,
)


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "knowledgelearningoffset.dbss"
_EMPTY = "-"


def _read_offsets(data: bytes) -> list[dict]:
    return [
        {"table": row.table, "source_id": row.source_id, "offset": row.offset, "size": row.size}
        for row in parse_knowledgelearning_offset_records(data)
    ]


def knowledge_learning_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("source_id", "sourceId"),
            OffsetColumn("table", "table"),
            offset_column("offset", "dbssOffset"),
            size_column("size", "size"),
        ],
        _read_offsets,
    )


class KnowledgeLearningHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR)["columns"]
        return [
            Column(cols["sourceId"], "num", sort_key="source_id"),
            Column(cols["sourceType"], sort_key="source_type"),
            Column(cols["sourceName"], sort_key="source_name"),
            Column(cols["knowledgeId"], "num", sort_key="card_id"),
            Column(cols["knowledgeName"], sort_key="card_name"),
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

        values = load_handler_strings(self.lang, _LANG_DIR)["values"]
        character, item = values["character"], values["item"]
        has_loc = is_loc_loaded()

        records: list[dict] = []
        for record in parse_knowledgelearning_records(data, offset_raw):
            is_item = record.source_type == SOURCE_ITEM
            source_loc = LOC_ITEM_NAME if is_item else LOC_CHARACTER_NAME
            records.append({
                "table": record.table,
                "source_type": item if is_item else character,
                "source_id": record.source_id,
                "source_name": loc_text(source_loc, record.source_id) if has_loc else "",
                "card_id": record.card_id,
                "card_name": knowledge_name(record.card_id),
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
        with_names = sum(1 for r in records if r["card_name"])
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records), with_names=with_names)

        rows = [
            [
                e(r["source_id"]),
                e(r["source_type"]),
                e(r["source_name"] or _EMPTY),
                e(r["card_id"]),
                e(r["card_name"] or _EMPTY),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
