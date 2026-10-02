from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.character import character_name
from _common.html import Column, e, join_limited, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded
from _dbss.characterspawntype.role_labels import role_label, role_label_overrides, role_tooltip, spawn_type_name
from _dbss.detail_dialog.lease import lease_text
from .leases import character_leases
from .parser import parse_npcsimply_records


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"
_LIST_PREVIEW_ITEMS = 3


def _kind_cell(record: dict) -> str:
    """The role's display name, with its enum name and value on hover."""
    return f'<span title="{e(role_tooltip(record["kind"]))}">{e(record["kind_label"])}</span>'


def _lease_fields(record: dict, has_loc: bool) -> dict:
    """The stored lease (`None` without one, so it sorts last) and every known lease as text."""
    item_id = record["lease_item_id"]
    leases = character_leases(record["character_id"], item_id, record["lease_cost"])
    return {
        "lease_item_id": item_id or None,
        "lease_cost": record["lease_cost"] if item_id else None,
        "leases": [lease_text(lease, has_loc) for lease in leases],
        # Empty sorts last.
        "lease_count": len(leases) or None,
    }


class NpcSimplyBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("characterId", "Character ID"), "num", sort_key="character_id"),
            Column(cols.get("name", "Name (EN)"), sort_key="name"),
            Column(cols.get("kind", "Kind"), sort_key="kind_label"),
            Column(cols.get("nameKr", "Name (KR)"), sort_key="name_kr"),
            Column(cols.get("role", "Role"), sort_key="role_kr"),
            Column(cols.get("knowledgeId", "Knowledge ID"), "num", sort_key="knowledge_id"),
            Column(cols.get("leases", "Leases"), sort_key="lease_count"),
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
        has_loc = is_loc_loaded()
        role_labels = role_label_overrides(self.lang)
        return [
            {
                **record,
                **_lease_fields(record, has_loc),
                "name": character_name(record["character_id"]),
                "kind_name": spawn_type_name(record["kind"]),
                "kind_label": role_label(record["kind"], role_labels),
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
                _kind_cell(record),
                e(record["name_kr"] or _EMPTY),
                e(record["role_kr"]),
                e(_EMPTY if record["knowledge_id"] is None else record["knowledge_id"]),
                e(join_limited(record["leases"], _LIST_PREVIEW_ITEMS) or _EMPTY),
                e(record["script"]),
            ]
            for record in slice_
        ]

        return table(meta, self._columns(), rows)
