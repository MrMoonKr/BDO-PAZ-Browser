from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.html import Column, e, sort_keys, table
from _common.lang import handler_text, load_handler_strings
from _common.zodiacsign.loc import zodiac_name
from _common.zodiacsign.parser import parse_zodiacsign_records
from .parser import parse_zodiacsignindex_records


_LANG_DIR = Path(__file__).parent / "lang"


class ZodiacSignIndexHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("zodiacId", "Zodiac ID"), "num", sort_key="zodiac_id"),
            Column(cols.get("name", "Name"), sort_key="name"),
        ]

    def sortable_fields(self) -> tuple[str, ...]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        if folder == entry.internal_path:
            return ["zodiacsign.dbss"]
        return [f"{folder}/zodiacsign.dbss"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        zodiacsign_raw = companions.get("zodiacsign.dbss")
        if zodiacsign_raw is None:
            raise ValueError("zodiacsign.dbss companion not found.")

        records = parse_zodiacsignindex_records(data)
        korean_names = {
            rec["zodiac_id"]: rec["constellation_name"] for rec in parse_zodiacsign_records(zodiacsign_raw)
        }

        result: list[dict] = []
        for rec in records:
            zodiac_id = rec["zodiac_id"]
            result.append({
                "slot": rec["slot"],
                "zodiac_id": zodiac_id,
                "name": zodiac_name(zodiac_id, korean_names.get(zodiac_id, "")),
                "known": zodiac_id in korean_names,
            })

        return result

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = handler_text(self.lang, _LANG_DIR, "meta.count", count=len(records))
        rows = [
            [e(r["zodiac_id"]), e(r["name"])]
            for r in slice_
        ]
        return table(meta, self._columns(), rows)
