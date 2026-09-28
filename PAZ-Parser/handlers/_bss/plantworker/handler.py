from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, icon_cell, sort_keys, table
from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags
from .display import LUCK_SCALE, MOVE_SPEED_SCALE, WORK_SPEED_SCALE, format_stat, worker_name_cell
from .grade import worker_grade
from .parser import parse_plantworker_records


_LANG_DIR = Path(__file__).parent / "lang"


def _worker_name(worker_id: int) -> str:
    if not is_loc_loaded():
        return ""
    return strip_pa_tags(loc_lookup(6, worker_id))


class PlantWorkerBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("workerId", "Worker ID"), "num", sort_key="worker_id"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("name", "Name"), sort_key="name"),
            Column(cols.get("nextWorkerId", "Next Tier"), "num", sort_key="next_worker_id"),
            Column(cols.get("moveSpeed", "Move"), "num", sort_key="move_speed"),
            Column(cols.get("stamina", "Stamina"), "num", sort_key="stamina"),
            Column(cols.get("luck", "Luck"), "num", sort_key="luck"),
            Column(cols.get("baseWorkSpeed", "Work Speed"), "num", sort_key="base_work_speed"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records: list[dict] = []
        for record in parse_plantworker_records(data):
            row = dict(record)
            row["name"] = _worker_name(record["worker_id"])
            row["worker_grade"] = worker_grade(
                record["grade_class"], record["worker_id"], row["name"]
            )
            # 0 means the last tier. None renders a dash and sorts last.
            row["next_worker_id"] = record["next_worker_id"] or None
            records.append(row)
        return records

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        named = sum(1 for record in records if record.get("name"))
        meta = f"{len(records):,} worker records"
        if named:
            meta += f" · {named:,} with LOC names"

        rows = [
            [
                e(record["worker_id"]),
                icon_cell(record.get("icon_path") or f"#{record['icon_index']}"),
                worker_name_cell(record.get("name"), record.get("worker_grade")),
                e(record["next_worker_id"] or "-"),
                e(format_stat(record["move_speed"], MOVE_SPEED_SCALE)),
                e(record["stamina"]),
                e(format_stat(record["luck"], LUCK_SCALE)),
                e(format_stat(record["base_work_speed"], WORK_SPEED_SCALE)),
            ]
            for record in slice_
        ]

        return table(meta, self._columns(), rows)
