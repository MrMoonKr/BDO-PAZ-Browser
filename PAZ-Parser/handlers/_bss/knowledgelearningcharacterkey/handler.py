from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.character import character_name
from _common.html import Column, e, sort_keys, table, text_list_cell
from _common.knowledge import knowledge_name
from _common.lang import handler_text, load_handler_strings
from .parser import parse_knowledgelearningcharacterkey


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"
_LIST_PREVIEW_ITEMS = 3


def _character(character_id: int) -> str:
    """`10263 Wild Herb`, or the bare ID when LOC has no name."""
    return f"{character_id} {character_name(character_id)}".strip()


class KnowledgeLearningCharacterKeyBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR)["columns"]
        return [
            Column(cols["knowledgeId"], "num", sort_key="card_id"),
            Column(cols["knowledgeName"], sort_key="card_name"),
            Column(cols["characterCount"], "num", sort_key="character_count"),
            Column(cols["characters"]),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return [
            {
                "card_id": card.card_id,
                "card_name": knowledge_name(card.card_id),
                "character_count": len(card.character_ids),
                "character_ids": list(card.character_ids),
                "characters": [_character(character_id) for character_id in card.character_ids],
            }
            for card in parse_knowledgelearningcharacterkey(data)
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        character_total = sum(r["character_count"] for r in records)
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records), character_total=character_total)

        rows = [
            [
                e(r["card_id"]),
                e(r["card_name"] or _EMPTY),
                e(r["character_count"]),
                text_list_cell(r["characters"], _LIST_PREVIEW_ITEMS),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
