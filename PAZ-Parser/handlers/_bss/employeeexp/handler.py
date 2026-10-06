from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import handler_text, load_handler_strings
from _bss.employeestaticstatus.display import stat_labels
from .display import growth_text, top_levels
from .parser import parse_employeeexp_records


_LANG_DIR = Path(__file__).parent / "lang"
_EMPTY = "-"


def _display_record(record: dict, top_level: int, labels: Mapping[int, str]) -> dict:
    """The parsed row plus its display fields.

    The top level stores a placeholder EXP with no next level to reach, so its
    `exp_to_next_level` is None (sorts last, shows a dash); `exp_raw` keeps the
    stored value for export.
    """
    is_max_level = record["level"] == top_level
    return {
        **record,
        "exp_to_next_level": None if is_max_level else record["exp_to_next_level"],
        "exp_raw": record["exp_to_next_level"],
        "is_max_level": is_max_level,
        "growth": growth_text(record["growth_dice"], labels),
    }


class EmployeeExpBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR)["columns"]
        return [
            Column(cols["employeeKey"], "num", sort_key="employee_key"),
            Column(cols["level"], "num", sort_key="level"),
            Column(cols["expToNextLevel"], "num", sort_key="exp_to_next_level"),
            Column(cols["growth"], sort_key="growth"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records = parse_employeeexp_records(data)
        top = top_levels(records)
        # The file runs level by level; keep each sailor's levels together.
        ordered = sorted(records, key=lambda record: (record["employee_key"], record["level"]))
        labels = stat_labels(self.lang)
        return [_display_record(record, top[record["employee_key"]], labels) for record in ordered]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        sailors = len({record["employee_key"] for record in records})
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records), sailors=sailors)
        rows = [
            [
                e(record["employee_key"]),
                e(record["level"]),
                _EMPTY if record["exp_to_next_level"] is None else e(f"{record['exp_to_next_level']:,}"),
                e(record["growth"] or _EMPTY),
            ]
            for record in slice_
        ]
        return table(meta, self._columns(), rows)
