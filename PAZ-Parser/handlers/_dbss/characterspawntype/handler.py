from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler
from table_sort import TableSort, sort_order_by_values

from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags
from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings
from _common.pabr_offset import parse_pabr_offset_rows
from .parser import ROLE_COUNT, SPAWN_TYPE_NAMES, parse_characterspawntype_records

# Role columns sort by a virtual field, read from the record's role list.
_ROLE_FIELD_PREFIX = "role_"
_LANG_DIR = Path(__file__).parent / "lang"
_LOC_CHARACTER_NAME = 6


def _character_name(character_id: int) -> str:
    raw = loc_lookup(_LOC_CHARACTER_NAME, character_id)
    return strip_pa_tags(raw) if raw else ""


def _role_field(idx: int) -> str:
    return f"{_ROLE_FIELD_PREFIX}{idx:02d}"


def _role_column(idx: int) -> Column:
    # The client enum name is the header; the SpawnType value is on hover.
    return Column(SPAWN_TYPE_NAMES[idx], "num", f'title="SpawnType {idx}"', sort_key=_role_field(idx))


class CharacterSpawnTypeOffsetHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("offsetColumns", {})
        return [
            Column(cols.get("characterId", "Character ID"), "num", sort_key="character_id"),
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
        return [
            {"character_id": row.entry_id, "offset": row.offset, "size": row.size}
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
            [e(r["character_id"]), e(f"0x{r['offset']:08X}"), e(r["size"])]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)


class CharacterSpawnTypeHandler(PreviewHandler):
    def _columns(self, active_roles: Iterable[int], has_loc: bool) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        columns = [Column(cols.get("characterId", "Character ID"), "num", sort_key="character_id")]
        if has_loc:
            columns.append(Column(cols.get("nameEn", "Name (EN)"), sort_key="name_en"))
        columns.extend(_role_column(i) for i in active_roles)
        return columns

    def sortable_fields(self) -> frozenset[str]:
        # Every role and the name, so a saved sort survives either being hidden.
        return sort_keys(self._columns(range(ROLE_COUNT), has_loc=True))

    def _build_sort_order(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
        sort: TableSort,
    ) -> list[int]:
        if not sort.field.startswith(_ROLE_FIELD_PREFIX):
            return super()._build_sort_order(data, entry, companions, sort)

        role = int(sort.field.removeprefix(_ROLE_FIELD_PREFIX))
        records = self._all_records(data, entry, companions)
        return sort_order_by_values([r["roles"][role] for r in records], sort.descending)

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        has_loc = is_loc_loaded()
        return [
            {
                "character_id": r["character_id"],
                "name_en": _character_name(r["character_id"]) if has_loc else "",
                "roles": r["roles"],
            }
            for r in parse_characterspawntype_records(data)
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        active = [i for i in range(ROLE_COUNT) if any(r["roles"][i] for r in records)]
        has_loc = is_loc_loaded()

        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} records · {len(active)} active role columns"

        rows = []
        for r in slice_:
            row = [e(r["character_id"])]
            if has_loc:
                row.append(e(r["name_en"]))
            for i in active:
                row.append("1" if r["roles"][i] else "")
            rows.append(row)

        return table(meta, self._columns(active, has_loc), rows)
