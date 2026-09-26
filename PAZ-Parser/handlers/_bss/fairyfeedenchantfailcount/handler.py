from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import load_handler_strings
from .parser import parse_fairyfeedenchantfailcount_records


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"


class FairyFeedEnchantFailCountBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("groupId", "Group ID"), "num", sort_key="group_id"),
            Column(cols.get("subKey", "Sub Key"), "num", sort_key="sub_key"),
            Column(cols.get("valueA", "Value A"), "num", sort_key="value_a"),
            Column(cols.get("valueB", "Value B"), "num", sort_key="value_b"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records = parse_fairyfeedenchantfailcount_records(data)
        for record in records:
            # Sub key 0 means none. None renders a dash and sorts last.
            record["sub_key"] = record["sub_key"] or None
        return records

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        groups = len({record["group_id"] for record in records})
        meta = f"{len(records):,} entries across {groups} groups"

        rows = [
            [
                e(record["group_id"]),
                e(record["sub_key"] or _EMPTY),
                e(f"{record['value_a']:,}"),
                e(f"{record['value_b']:,}"),
            ]
            for record in slice_
        ]

        return table(meta, self._columns(), rows)
