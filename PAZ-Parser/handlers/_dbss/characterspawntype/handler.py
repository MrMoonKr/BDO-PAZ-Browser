from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler
from table_sort import TableSort, sort_order_by_values

from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags
from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings
from .parser import (
    parse_characterspawntype_records,
    parse_characterspawntypeoffset_records,
)

_NUM_FLAGS = 44
# Flag columns sort by a virtual field, read from the record's flag list.
_FLAG_FIELD_PREFIX = "flag_"
_LANG_DIR = Path(__file__).parent / "lang"

_FLAG_NAMES: dict[int, str] = {
    1: "villa_vendor",
    12: "quest_variant",
    14: "battlefield_vendor",
    15: "wandering_merchant",
    18: "specialty_shop",
    22: "guild_vendor",
    30: "event_npc",
    32: "timed_spawn",
    43: "main_quest",
}

def _lookup_name(entity_id: int) -> str:
    name = loc_lookup(6, entity_id)
    if name:
        return strip_pa_tags(name)
    if entity_id >> 16:
        for t in (0, 50):
            name = loc_lookup(t, entity_id)
            if name:
                return strip_pa_tags(name)
    return ""


def _flag_field(idx: int) -> str:
    return f"{_FLAG_FIELD_PREFIX}{idx:02d}"


def _flag_column(idx: int) -> Column:
    name = _FLAG_NAMES.get(idx, "")
    extra = f'title="{name}"' if name else ""
    return Column(f"f{idx:02d}", "num", extra, sort_key=_flag_field(idx))


def _entity_id_cell(entity_id: int) -> str:
    return f'<span title="0x{entity_id:08X}">{e(entity_id)}</span>'


class CharacterSpawnTypeOffsetHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("offsetColumns", {})
        return [
            Column(cols.get("idLow16", "ID Low16"), "num", sort_key="id_low16"),
            Column(cols.get("byteOffset", "Byte Offset"), "num", sort_key="offset"),
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
        return parse_characterspawntypeoffset_records(data)

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
            [e(r["id_low16"]), e(f"0x{r['offset']:08X}"), e(r["size"])]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)


class CharacterSpawnTypeHandler(PreviewHandler):
    def _columns(self, active_flags: Iterable[int], has_loc: bool) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        columns = [Column(cols.get("entityId", "entity_id"), "num", sort_key="entity_id")]
        if has_loc:
            columns.append(Column(cols.get("nameEn", "Name (EN)"), sort_key="name_en"))
        columns.extend(_flag_column(i) for i in active_flags)
        return columns

    def sortable_fields(self) -> frozenset[str]:
        # Every flag and the name, so a saved sort survives either being hidden.
        return sort_keys(self._columns(range(_NUM_FLAGS), has_loc=True))

    def _build_sort_order(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
        sort: TableSort,
    ) -> list[int]:
        if not sort.field.startswith(_FLAG_FIELD_PREFIX):
            return super()._build_sort_order(data, entry, companions, sort)

        flag = int(sort.field.removeprefix(_FLAG_FIELD_PREFIX))
        records = self._all_records(data, entry, companions)
        return sort_order_by_values([r["flags"][flag] for r in records], sort.descending)

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        raw = parse_characterspawntype_records(data)
        loc = is_loc_loaded()
        return [
            {
                "entity_id": r["entity_id"],
                "name_en": _lookup_name(r["entity_id"]) if loc else "",
                "flags": r["flags"],
            }
            for r in raw
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        active = [i for i in range(_NUM_FLAGS) if any(r["flags"][i] for r in records)]
        has_loc = is_loc_loaded()

        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} records · {len(active)} active flag columns"

        rows = []
        for r in slice_:
            row = [_entity_id_cell(r["entity_id"])]
            if has_loc:
                row.append(e(r["name_en"]))
            for i in active:
                row.append("1" if r["flags"][i] else "")
            rows.append(row)

        return table(meta, self._columns(active, has_loc), rows)
