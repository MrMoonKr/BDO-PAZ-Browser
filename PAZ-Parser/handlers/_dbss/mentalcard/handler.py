from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.character import character_name
from _common.html import Column, e, icon_cell, sort_keys, table, text_list_cell
from _common.knowledge import LOC_KNOWLEDGE, knowledge_name, theme_name
from _common.lang import handler_text, load_handler_strings
from _common.loc import is_loc_loaded, loc_tagged
from _common.pa_text import pa_cell, pa_fields, pa_line_cell
from _common.lookup_index import IndexKind, lookup
from _common.offset_table import (
    OffsetColumn,
    OffsetTableHandler,
    offset_column,
    offset_records,
    size_column,
)
from .combo import combo_text, has_combo
from .parser import MentalCardRecord, parse_mentalcard_offset_records, parse_mentalcard_records


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "mentalcardoffset.dbss"
# LOC type 34 sub-fields of the description and the "how to obtain" text.
_LOC_DESCRIPTION = 1
_LOC_ACQUISITION = 2
_EMPTY = "-"
_LIST_PREVIEW_ITEMS = 3


def _position_text(position: tuple[float, float, float]) -> str:
    """Whole-number `x, y, z`, or "" for the all-zero "no position" value."""
    if not any(position):
        return ""
    return ", ".join(str(round(axis)) for axis in position)


def _combo_fields(record: MentalCardRecord) -> dict:
    """Raw combo values and the tooltip text; all `None` without a combo, so they sort last."""
    if not has_combo(record):
        return {"combo_text": None, "buff_type": None, "combo_value": None, "valid_turn": None, "apply_turn": None}
    return {
        "combo_text": combo_text(record),
        "buff_type": record.buff_type,
        "combo_value": round(record.varied_value),
        "valid_turn": record.valid_turn,
        "apply_turn": record.apply_turn,
    }


def _learned_from(card_id: int) -> list[str]:
    """Distinct names of the characters that grant the card, in ID order.

    Copies of one NPC share a name, so most cards reduce to a single name. A
    character without a LOC name shows its ID. Empty when the index is not
    loaded or no character grants the card.
    """
    characters = lookup(IndexKind.KNOWLEDGE_CHARACTERS, card_id)
    if not isinstance(characters, tuple):
        return []

    names = (character_name(character_id) or str(character_id) for character_id in characters)
    return list(dict.fromkeys(names))


def mental_card_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("card_id", "cardId"),
            offset_column("dbss_offset", "dbssOffset"),
            size_column("size", "size"),
        ],
        offset_records(parse_mentalcard_offset_records, "card_id", "dbss_offset"),
    )


class MentalCardHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR)["columns"]
        return [
            Column(cols["knowledgeId"], "num", sort_key="entry_id"),
            Column(cols["icon"], sort_key="icon_path"),
            Column(cols["knowledgeName"], sort_key="entry_name"),
            Column(cols["categoryId"], "num", sort_key="node_id"),
            Column(cols["categoryName"], sort_key="node_name"),
            Column(cols["description"], sort_key="description"),
            Column(cols["minFavor"], "num", sort_key="min_favor"),
            Column(cols["maxFavor"], "num", sort_key="max_favor"),
            Column(cols["interest"], "num", sort_key="interest"),
            Column(cols["combo"], sort_key="combo_text"),
            Column(cols["obtain"], sort_key="obtain"),
            Column(cols["learnedFrom"]),
            Column(cols["position"]),
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

        has_loc = is_loc_loaded()
        return [
            {
                "entry_id": record.card_id,
                # LOC first; the Korean source name stands in without it.
                "entry_name": knowledge_name(record.card_id) or record.name_kr,
                "node_id": record.theme_id,
                "node_name": theme_name(record.theme_id) if has_loc else "",
                # Stored as floats but always whole numbers.
                "min_favor": round(record.min_favor),
                "max_favor": round(record.max_favor),
                "interest": round(record.interest),
                **_combo_fields(record),
                "icon_path": record.icon_path,
                **pa_fields(
                    "description",
                    (loc_tagged(LOC_KNOWLEDGE, record.card_id, _LOC_DESCRIPTION) if has_loc else "")
                    or record.description_kr,
                ),
                **pa_fields(
                    "obtain",
                    (loc_tagged(LOC_KNOWLEDGE, record.card_id, _LOC_ACQUISITION) if has_loc else "")
                    or record.acquisition_kr,
                ),
                "learned_from": _learned_from(record.card_id),
                "position": list(record.position),
                "position_text": _position_text(record.position),
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
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records), with_node_name=with_node_name)

        rows = [
            [
                e(r["entry_id"]),
                icon_cell(r["icon_path"]),
                e(r["entry_name"] or _EMPTY),
                e(r["node_id"]),
                e(r["node_name"] or _EMPTY),
                pa_line_cell(r, "description"),
                e(r["min_favor"]),
                e(r["max_favor"]),
                e(r["interest"]),
                e(r["combo_text"] or _EMPTY),
                pa_cell(r, "obtain"),
                text_list_cell(r["learned_from"], _LIST_PREVIEW_ITEMS) or _EMPTY,
                e(r["position_text"] or _EMPTY),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
