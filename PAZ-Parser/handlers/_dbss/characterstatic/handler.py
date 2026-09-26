from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags
from _common.html import Column, e, error, icon_cell, sort_keys, table
from _common.icon_index import IconKind, icon_path
from _common.lang import load_handler_strings
from .parser import (
    parse_characterstaticoffset_records,
    parse_characterstatic_records,
)

_LANG_DIR = Path(__file__).parent / "lang"


class CharacterStaticOffsetHandler(PreviewHandler):
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
        return parse_characterstaticoffset_records(data)

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


class CharacterStaticHandler(PreviewHandler):
    def _columns(self, has_loc: bool) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        columns = [
            Column(cols.get("characterId", "Character ID"), "num", sort_key="character_id"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
        ]
        if has_loc:
            columns.append(Column(cols.get("nameEn", "Name (EN)"), sort_key="name_en"))
        columns += [
            Column(cols.get("script", "Script"), sort_key="script"),
            Column(cols.get("knowledgeId", "Knowledge ID"), "num", sort_key="knowledge_id"),
            Column(cols.get("payloadSize", "Payload Size"), "num", sort_key="payload_size"),
            Column(cols.get("unknownType", "Unknown Type"), "num", sort_key="unknown_type"),
        ]
        return columns

    def sortable_fields(self) -> frozenset[str]:
        # Includes the name, so a saved sort survives LOC not being loaded.
        return sort_keys(self._columns(has_loc=True))

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [
            f"{folder}/characterstaticoffset.dbss",
            f"{folder}/languagedata_en.loc",
        ]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get("characterstaticoffset.dbss")
        if not offset_raw:
            return [{"_error": "characterstaticoffset.dbss companion not found"}]

        offset_records = parse_characterstaticoffset_records(offset_raw)
        raw_records = parse_characterstatic_records(data, offset_records)
        loc = is_loc_loaded()

        result: list[dict] = []
        for r in raw_records:
            name = ""
            if loc:
                raw_name = loc_lookup(6, r["character_id"])
                name = strip_pa_tags(raw_name) if raw_name else ""
            result.append(
                {
                    "character_id": r["character_id"],
                    "icon_path": icon_path(IconKind.CHARACTER, r["character_id"]),
                    "name_en": name,
                    "script": r["script"],
                    "knowledge_id": r["knowledge_id"],
                    "payload_size": r["payload_size"],
                    "unknown_type": r["unknown_type"],
                }
            )
        return result

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        if records and "_error" in records[0]:
            return error(records[0]["_error"])

        has_loc = is_loc_loaded()

        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} records"

        rows: list[list[str]] = []
        for r in slice_:
            row: list[str] = [
                e(r["character_id"]),
                icon_cell(r["icon_path"]) if r["icon_path"] else "-",
            ]
            if has_loc:
                row.append(e(r["name_en"]))
            row.append(e(r["script"]))
            row.append(e(r["knowledge_id"]) if r["knowledge_id"] is not None else "")
            row.append(e(r["payload_size"]))
            row.append(e(r["unknown_type"]))
            rows.append(row)

        return table(meta, self._columns(has_loc), rows)
