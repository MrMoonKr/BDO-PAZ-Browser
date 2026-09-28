from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, icon_cell, join_limited, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded, loc_text
from _common.lookup_index import IndexKind, lookup
from .parser import parse_mentalcard_offset_records, parse_mentalcard_records


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "mentalcardoffset.dbss"
_LOC_CHARACTER_NAME = 6
_LOC_THEME = 9
_LOC_KNOWLEDGE = 34
# LOC type 34 sub-field holding the English "how to obtain" text.
_LOC_ACQUISITION = 2
_EMPTY = "-"
_LIST_PREVIEW_ITEMS = 3


def _position_text(position: tuple[float, float, float]) -> str:
    """Whole-number `x, y, z`, or "" for the all-zero "no position" value."""
    if not any(position):
        return ""
    return ", ".join(str(round(axis)) for axis in position)


def _learned_from(card_id: int, has_loc: bool) -> list[str]:
    """Distinct names of the characters that grant the card, in ID order.

    Copies of one NPC share a name, so most cards reduce to a single name. A
    character without a LOC name shows its ID. Empty when the index is not
    loaded or no character grants the card.
    """
    characters = lookup(IndexKind.KNOWLEDGE_CHARACTERS, card_id)
    if not isinstance(characters, tuple):
        return []

    names = (
        (loc_text(_LOC_CHARACTER_NAME, character_id) if has_loc else "") or str(character_id)
        for character_id in characters
    )
    return list(dict.fromkeys(names))


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
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("knowledgeName", "Knowledge Name"), sort_key="entry_name"),
            Column(cols.get("categoryId", "Category ID"), "num", sort_key="node_id"),
            Column(cols.get("categoryName", "Category Name"), sort_key="node_name"),
            Column(cols.get("minFavor", "Min Favor"), "num", sort_key="min_favor"),
            Column(cols.get("maxFavor", "Max Favor"), "num", sort_key="max_favor"),
            Column(cols.get("interest", "Interest"), "num", sort_key="interest"),
            Column(cols.get("obtain", "Obtain"), sort_key="obtain"),
            Column(cols.get("learnedFrom", "Learned From")),
            Column(cols.get("position", "Position")),
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
                "entry_name": (loc_text(_LOC_KNOWLEDGE, record.card_id) if has_loc else "")
                or record.name_kr,
                "node_id": record.theme_id,
                "node_name": loc_text(_LOC_THEME, record.theme_id) if has_loc else "",
                # Stored as floats but always whole numbers.
                "min_favor": round(record.min_favor),
                "max_favor": round(record.max_favor),
                "interest": round(record.interest),
                "icon_path": record.icon_path,
                "obtain": (
                    loc_text(_LOC_KNOWLEDGE, record.card_id, _LOC_ACQUISITION) if has_loc else ""
                )
                or record.acquisition_kr,
                "learned_from": _learned_from(record.card_id, has_loc),
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
        meta = f"{len(records):,} knowledge cards · {with_node_name:,} category names"

        rows = [
            [
                e(r["entry_id"]),
                icon_cell(r["icon_path"]),
                e(r["entry_name"] or _EMPTY),
                e(r["node_id"]),
                e(r["node_name"] or _EMPTY),
                e(r["min_favor"]),
                e(r["max_favor"]),
                e(r["interest"]),
                e(r["obtain"] or _EMPTY),
                e(join_limited(r["learned_from"], _LIST_PREVIEW_ITEMS) or _EMPTY),
                e(r["position_text"] or _EMPTY),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
