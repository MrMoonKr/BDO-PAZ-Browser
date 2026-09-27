from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags
from .parser import NODE_KIND_NAMES, parse_exploration_records


_LANG_DIR = Path(__file__).parent / "lang"
_LOC_NODE_NAME = 29
_LOC_CHARACTER_NAME = 6
_EMPTY = "-"


def _loc_text(str_type: int, key: int) -> str:
    return strip_pa_tags(loc_lookup(str_type, key) or "").strip()


def _kind_name(kind: int) -> str:
    return NODE_KIND_NAMES[kind] if kind < len(NODE_KIND_NAMES) else str(kind)


def _character(character_id: int, has_loc: bool) -> str:
    """ID with its LOC name, or "" when the field is 0."""
    if not character_id:
        return ""
    name = _loc_text(_LOC_CHARACTER_NAME, character_id) if has_loc else ""
    return f"{character_id} {name}".strip()


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
        strings = load_handler_strings(self.lang, _LANG_DIR).get("values", {})
        main, sub = strings.get("main", "Main"), strings.get("sub", "Sub")

        return [
            {
                **record,
                # LOC type 29 is the display name; the Korean source name
                # stands in when LOC is not loaded or has no entry.
                "node_name": (_loc_text(_LOC_NODE_NAME, record["node_key"]) if has_loc else "")
                or record["name_kr"],
                "kind": _kind_name(record["node_kind"]),
                "main_sub": sub if record["is_sub_node"] else main,
                # Empty sorts last and exports as an empty cell.
                "manager": _character(record["manager_id"], has_loc) or None,
                "representative": _character(record["representative_id"], has_loc) or None,
            }
            for record in parse_exploration_records(data)
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
            ]
            for record in slice_
        ]

        return table(meta, self._columns(), rows)
