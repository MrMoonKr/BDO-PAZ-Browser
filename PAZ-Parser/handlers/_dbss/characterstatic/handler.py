from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags
from _common.html import Column, e, error, icon_cell, sort_keys, table
from _common.icon_index import IconKind, icon_path
from _common.lang import load_handler_strings
from _common.pabr_offset import parse_pabr_offset_rows
from .parser import NO_CLASS_TYPE, parse_characterstatic_records

_LANG_DIR = Path(__file__).parent / "lang"
_LOC_CHARACTER_NAME = 6
# The low byte of `npc_kind` is the character kind; the higher bits are unmapped flags.
_NPC_KIND_LOW_MASK = 0xFF


def _character_name(character_id: int) -> str:
    raw = loc_lookup(_LOC_CHARACTER_NAME, character_id)
    return strip_pa_tags(raw) if raw else ""


def _optional(value: int | None) -> str:
    return e(value) if value is not None else ""


class CharacterStaticOffsetHandler(PreviewHandler):
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
            Column(cols.get("actionScript", "Action Script"), sort_key="action_script"),
            Column(cols.get("conditionScript", "Condition"), sort_key="condition_script"),
            Column(cols.get("knowledgeId", "Knowledge ID"), "num", sort_key="knowledge_id"),
            Column(cols.get("npcKind", "NPC Kind"), "num", sort_key="npc_kind_low"),
            Column(cols.get("classType", "Class Type"), "num", sort_key="class_type"),
            Column(cols.get("model", "Model"), sort_key="model_path"),
            Column(cols.get("payloadSize", "Payload Size"), "num", sort_key="payload_size"),
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

        try:
            raw_records = parse_characterstatic_records(data, parse_pabr_offset_rows(offset_raw))
        except ValueError as ex:
            return [{"_error": f"characterstatic.dbss could not be parsed: {ex}"}]

        has_loc = is_loc_loaded()
        return [
            {
                "character_id": r["character_id"],
                "icon_path": icon_path(IconKind.CHARACTER, r["character_id"]),
                "name_en": _character_name(r["character_id"]) if has_loc else "",
                "action_script": r["action_script"],
                "condition_script": r["condition_script"],
                "knowledge_id": r["knowledge_id"],
                "npc_kind": r["npc_kind"],
                "npc_kind_low": r["npc_kind"] & _NPC_KIND_LOW_MASK,
                # 101 means "not a player character"; None sorts last.
                "class_type": None if r["class_type"] == NO_CLASS_TYPE else r["class_type"],
                "model_path": r["model_path"],
                "payload_size": r["payload_size"],
            }
            for r in raw_records
        ]

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
            row.append(e(r["action_script"]))
            row.append(e(r["condition_script"]))
            row.append(_optional(r["knowledge_id"]))
            row.append(e(r["npc_kind_low"]))
            row.append(_optional(r["class_type"]))
            row.append(e(r["model_path"] or "-"))
            row.append(e(r["payload_size"]))
            rows.append(row)

        return table(meta, self._columns(has_loc), rows)
