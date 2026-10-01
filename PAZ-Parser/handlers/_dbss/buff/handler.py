from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.buff import buff_loc_description
from _common.duration import format_duration
from _common.html import Column, e, icon_cell, sort_keys, table
from _common.item_key import item_key_list_cell, item_key_text
from _common.lang import load_handler_strings
from _common.loc import strip_pa_tags
from _common.lookup_index import IndexKind, index_entries, lookup
from _common.pabr_offset import parse_pabr_offset_rows
from .effect import effect_text
from .parser import PARAM_COUNT, parse_buff_records
from .title import extract_title, title_leaders


_LANG_DIR = Path(__file__).parent / "lang"
_OFFSET_FILE = "buffoffset.dbss"

_EMPTY = "-"
_SHOWN_PARAMS = 3
_LIST_PREVIEW_ITEMS = 3


def _raw_description(buff_id: int, description_kr: str) -> str:
    """English description from LOC with PA tags intact, else the inline Korean."""
    return buff_loc_description(buff_id) or description_kr


def _applying_items(buff_id: int) -> list[int]:
    """Base items whose skills apply the buff, from the BUFF_ITEMS lookup index."""
    item_ids = lookup(IndexKind.BUFF_ITEMS, buff_id)
    return list(item_ids) if isinstance(item_ids, tuple) else []


def _skill_buff_lists() -> list[tuple[int, ...]]:
    """The buffs each skill applies together, from the SKILL_BUFFS lookup index."""
    return [buff_ids for buff_ids in index_entries(IndexKind.SKILL_BUFFS).values() if isinstance(buff_ids, tuple)]


def _title_cell(record: dict) -> str:
    """The title; one taken from the headline buff it is applied with is dimmed."""
    if not record["title"]:
        return _EMPTY
    if record["title_buff_id"] == record["buff_id"]:
        return e(record["title"])
    tooltip = f"Title of buff {record['title_buff_id']}"
    return f'<span class="inherited-cell" title="{e(tooltip)}">{e(record["title"])}</span>'


class BuffOffsetHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("offsetColumns", {})
        return [
            Column(cols.get("buffId", "Buff ID"), "num", sort_key="buff_id"),
            Column(cols.get("dataOffset", "Data Offset"), "num", sort_key="offset"),
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
            {"buff_id": row.entry_id, "offset": row.offset, "size": row.size}
            for row in parse_pabr_offset_rows(data)
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
            [e(r["buff_id"]), e(f"0x{r['offset']:08X}"), e(r["size"])]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)


def _add_inherited_titles(records: list[dict]) -> None:
    """Give untitled buffs the title of the headline buff they are applied with.

    `title_buff_id` names the buff whose description holds the title: the
    buff itself, the headline buff, or None without a title.
    """
    own_titles = {r["buff_id"]: r["title"] for r in records if r["title"]}
    leaders = title_leaders(_skill_buff_lists(), own_titles)
    for record in records:
        buff_id = record["buff_id"]
        title_buff_id = buff_id if buff_id in own_titles else leaders.get(buff_id)
        record["title_buff_id"] = title_buff_id
        if title_buff_id is not None:
            record["title"] = own_titles[title_buff_id]


class BuffHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("buffId", "Buff ID"), "num", sort_key="buff_id"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("title", "Title"), sort_key="title"),
            Column(cols.get("name", "Internal Name"), sort_key="name"),
            Column(cols.get("description", "Description"), sort_key="description"),
            Column(cols.get("effect", "Effect"), sort_key="effect"),
            Column(cols.get("appliedBy", "Applied By"), sort_key="applied_by_count"),
            Column(cols.get("level", "Level"), "num", sort_key="level"),
            Column(cols.get("effectType", "Effect Type"), "num", sort_key="effect_type"),
            Column(cols.get("duration", "Duration"), "num", sort_key="duration_ms"),
            *(
                Column(cols.get(f"param{index}", f"Param {index}"), "num", sort_key=f"param_{index}")
                for index in range(1, _SHOWN_PARAMS + 1)
            ),
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
        offset_data = companions.get(_OFFSET_FILE)
        if not offset_data:
            raise ValueError(f"{_OFFSET_FILE} companion not found")

        records = parse_buff_records(data, parse_pabr_offset_rows(offset_data))
        for record in records:
            raw = _raw_description(record["buff_id"], record["description_kr"])
            record["title"] = extract_title(raw)
            record["description"] = strip_pa_tags(raw).strip()
            record["effect"] = effect_text(
                record["effect_type"],
                [record[f"param_{index}"] for index in range(1, PARAM_COUNT + 1)],
            )
            record["duration"] = format_duration(record["duration_ms"])
            # 0 means no duration. None renders a dash and sorts last.
            record["duration_ms"] = record["duration_ms"] or None
            item_ids = _applying_items(record["buff_id"])
            record["applied_by_item_ids"] = item_ids
            record["applied_by"] = [item_key_text(item_id) for item_id in item_ids]
            record["applied_by_count"] = len(item_ids) or None
        _add_inherited_titles(records)
        return records

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} buffs"
        rows = [
            [
                e(r["buff_id"]),
                icon_cell(r["icon_path"]) if r["icon_path"] else _EMPTY,
                _title_cell(r),
                e(r["name"]),
                e(r["description"]) if r["description"] else _EMPTY,
                e(r["effect"]) if r["effect"] else _EMPTY,
                item_key_list_cell(r["applied_by_item_ids"], _LIST_PREVIEW_ITEMS) or _EMPTY,
                e(r["level"]),
                e(r["effect_type"]),
                e(r["duration"]) if r["duration"] else _EMPTY,
                *(e(r[f"param_{index}"]) for index in range(1, _SHOWN_PARAMS + 1)),
            ]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
