from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.character import character_name
from _common.html import Column, e, sort_keys, table, text_list_cell
from _common.knowledge import knowledge_name
from _common.lang import load_handler_strings
from _common.node import node_name
from _bwp.waypoint.worldmap import worldmap_companion, worldmap_links
from .connections import connection_fields
from .parser import NODE_KIND_NAMES, parse_exploration_records


_LANG_DIR = Path(__file__).parent / "lang"
_LIST_PREVIEW_ITEMS = 6
_EMPTY = "-"


def _kind_name(kind: int) -> str:
    return NODE_KIND_NAMES[kind] if kind < len(NODE_KIND_NAMES) else str(kind)


def _character(character_id: int) -> str:
    """ID with its LOC name, or "" when the field is 0."""
    if not character_id:
        return ""
    return f"{character_id} {character_name(character_id)}".strip()


def _knowledge_names(knowledge_ids: list[int]) -> list[str]:
    """LOC type 34 card name per ID, or the bare ID when it has none."""
    return [knowledge_name(key) or str(key) for key in knowledge_ids]


class ExplorationBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("nodeKey", "Node Key"), "num", sort_key="node_key"),
            Column(cols.get("nodeName", "Node Name"), sort_key="node_name"),
            Column(cols.get("kind", "Kind"), sort_key="kind"),
            Column(cols.get("mainSub", "Main/Sub"), sort_key="main_sub"),
            Column(cols.get("contribution", "Contribution"), "num", sort_key="contribution"),
            Column(cols.get("manager", "Manager"), sort_key="manager"),
            Column(cols.get("representative", "Representative"), sort_key="representative"),
            Column(cols.get("radius", "Radius"), "num", sort_key="radius"),
            Column(cols.get("knowledge", "Knowledge"), "num", sort_key="knowledge_count"),
            Column(cols.get("knowledgeEntries", "Knowledge Entries")),
            Column(cols.get("connections", "Connections"), "num", sort_key="connection_count"),
            Column(cols.get("connectedNodes", "Connected Nodes")),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        return [worldmap_companion(entry)]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        strings = load_handler_strings(self.lang, _LANG_DIR).get("values", {})
        main, sub = strings.get("main", "Main"), strings.get("sub", "Sub")

        records: list[dict] = []
        for record in parse_exploration_records(data):
            knowledge_names = _knowledge_names(record["knowledge_ids"])
            records.append({
                **record,
                # LOC type 29 is the display name; the Korean source name
                # stands in when LOC is not loaded or has no entry.
                "node_name": node_name(record["node_key"]) or record["name_kr"],
                "kind": _kind_name(record["node_kind"]),
                "main_sub": sub if record["is_sub_node"] else main,
                # Empty sorts last and exports as an empty cell.
                "manager": _character(record["manager_id"]) or None,
                "representative": _character(record["representative_id"]) or None,
                "knowledge_count": len(record["knowledge_ids"]),
                "knowledge_names": knowledge_names,
                # Full list as text, so tab search and CSV export see every name.
                "knowledge_text": ", ".join(knowledge_names),
            })

        # Links name their nodes the way the Node Name column does.
        links = worldmap_links(companions)
        node_names = {record["node_key"]: record["node_name"] for record in records}
        return [
            {**record, **connection_fields(record["node_key"], links, node_names)}
            for record in records
        ]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} worldmap nodes"

        rows = [
            [
                e(record["node_key"]),
                e(record["node_name"] or _EMPTY),
                e(record["kind"]),
                e(record["main_sub"]),
                e(record["contribution"]),
                e(record["manager"] or _EMPTY),
                e(record["representative"] or _EMPTY),
                e(f"{record['radius']:.2f}"),
                e(record["knowledge_count"]),
                text_list_cell(record["knowledge_names"], _LIST_PREVIEW_ITEMS) or _EMPTY,
                e(record["connection_count"]),
                text_list_cell(record["connection_names"], _LIST_PREVIEW_ITEMS) or _EMPTY,
            ]
            for record in slice_
        ]

        return table(meta, self._columns(), rows)
