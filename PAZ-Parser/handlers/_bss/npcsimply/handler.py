from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import loc_text
from _dbss.characterspawntype.parser import SPAWN_TYPE_NAMES
from .parser import parse_npcsimply_records


_LANG_DIR = Path(__file__).parent / "lang"
_LOC_CHARACTER_NAME = 6
_EMPTY = "-"


def _kind_name(kind: int) -> str:
    return SPAWN_TYPE_NAMES[kind] if kind < len(SPAWN_TYPE_NAMES) else str(kind)


class NpcSimplyBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("characterId", "Character ID"), "num", sort_key="character_id"),
            Column(cols.get("name", "Name (EN)"), sort_key="name"),
            Column(cols.get("kind", "Kind"), sort_key="kind_name"),
            Column(cols.get("nameKr", "Name (KR)"), sort_key="name_kr"),
            Column(cols.get("role", "Role"), sort_key="role_kr"),
            Column(cols.get("knowledgeId", "Knowledge ID"), "num", sort_key="knowledge_id"),
            Column(cols.get("script", "Script"), sort_key="script"),
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
            {
                **record,
                "name": loc_text(_LOC_CHARACTER_NAME, record["character_id"]),
                "kind_name": _kind_name(record["kind"]),
            }
            for record in parse_npcsimply_records(data)
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} NPCs"

        rows = [
            [
                e(record["character_id"]),
                e(record["name"] or _EMPTY),
                e(record["kind_name"]),
                e(record["name_kr"] or _EMPTY),
                e(record["role_kr"]),
                e(_EMPTY if record["knowledge_id"] is None else record["knowledge_id"]),
                e(record["script"]),
            ]
            for record in slice_
        ]

        return table(meta, self._columns(), rows)
