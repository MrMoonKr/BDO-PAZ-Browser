from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.fairy import upgrade_step_label
from _common.html import Column, e, icon_cell, sort_keys, table
from _common.icon_index import IconKind, icon_path
from _common.lang import handler_text, load_handler_strings
from _common.item_key import item_name_tagged
from _common.pa_text import pa_cell, pa_fields
from .parser import parse_fairyupgraderate_records


_LANG_DIR = Path(__file__).parent / "lang"

_CHANCE_DECIMALS = 4


class FairyUpgradeRateBssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("step", "Step"), "num", sort_key="step"),
            Column(cols.get("upgrade", "Upgrade"), sort_key="upgrade"),
            Column(cols.get("icon", "Icon"), sort_key="icon_path"),
            Column(cols.get("item", "Item"), sort_key="item_name"),
            Column(cols.get("itemId", "Item ID"), "num", sort_key="item_id"),
            Column(cols.get("chancePerItem", "Chance / Item"), "num", sort_key="chance_pct"),
            Column(cols.get("ratePpm", "Rate (ppm)"), "num", sort_key="rate_ppm"),
            Column(cols.get("itemsForMax", "Items for Max"), "num", sort_key="items_for_max"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        records: list[dict] = []

        for record in parse_fairyupgraderate_records(data):
            row = dict(record)
            item_id = row["item_id"]
            row["upgrade"] = upgrade_step_label(row["step"])
            row.update(pa_fields("item_name", item_name_tagged(item_id)))
            row["icon_path"] = icon_path(IconKind.ITEM, item_id)
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
        steps = len({record["step"] for record in records})
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records), steps=steps)

        localized = sum(1 for record in records if record.get("item_name"))
        if localized:
            meta += handler_text(self.lang, _LANG_DIR, "meta.localized", localized=localized)

        rows = [
            [
                e(record["step"]),
                e(record["upgrade"] or record["step"]),
                icon_cell(record["icon_path"]),
                pa_cell(record, "item_name") if record["item_name"] else e(record["item_id"]),
                e(record["item_id"]),
                e(f"{round(record['chance_pct'], _CHANCE_DECIMALS):g}%"),
                e(f"{record['rate_ppm']:,}"),
                e(f"{record['items_for_max']:,}"),
            ]
            for record in slice_
        ]

        return table(meta, self._columns(), rows)
