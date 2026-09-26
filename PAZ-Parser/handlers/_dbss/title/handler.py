from __future__ import annotations

from pathlib import Path

from bdo_models import PazEntry
from bdo_preview import PreviewHandler

from _common.lang import load_handler_strings
from _common.loc import is_loc_loaded, loc_lookup, strip_pa_tags

from _common.binary import parse_offset_table
from _common.html import Column, color_cell, e, sort_keys, table
from .parser import extract_title_records


_LANG_DIR = Path(__file__).parent / "lang"

_CATEGORY_NAMES: dict[int, str] = {
    0: "World",
    1: "Combat",
    2: "Life Skill",
    3: "Fishing",
}


def _category_label(category_id: int) -> str:
    return _CATEGORY_NAMES.get(category_id, str(category_id))


def _title_cell(title: str, css_color: str) -> str:
    if not css_color:
        return e(title)

    return f'<span style="color:{e(css_color)}">{e(title)}</span>'


class TitleDbssHandler(PreviewHandler):
    def _columns(self) -> list[Column]:
        cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
        return [
            Column(cols.get("titleId", "Title ID"), "num", sort_key="title_id"),
            Column(cols.get("category", "Category"), sort_key="category"),
            Column(cols.get("titleColor", "Title Color"), sort_key="title_color_argb"),
            Column(cols.get("title", "Title"), sort_key="title"),
            Column(cols.get("titleRequirements", "Title Requirements"), sort_key="requirement"),
            Column(cols.get("special", "Special"), sort_key="is_special"),
            Column(cols.get("effect", "Effect"), sort_key="title_effect_name"),
        ]

    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(self._columns())

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/titleoffset.dbss"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        offset_raw = companions.get("titleoffset.dbss")
        if offset_raw is None:
            raise ValueError("titleoffset.dbss companion not found - cannot parse blocks.")

        offset_map = parse_offset_table(offset_raw)
        records = extract_title_records(data, offset_map)

        has_loc = is_loc_loaded()
        result: list[dict] = []
        for rec in records:
            row: dict = dict(rec)
            if has_loc:
                row["en_name"] = loc_lookup(1, rec["title_id"])
                row["en_req"] = strip_pa_tags(loc_lookup(1, rec["title_id"], 0, 0, 1))
            row["category"] = _category_label(rec["category_id"])
            row["title"] = strip_pa_tags(row.get("en_name") or rec["title_text_ko"])
            row["requirement"] = strip_pa_tags(row.get("en_req") or rec["requirement_text_ko"])
            row["is_special"] = bool(rec["title_color_argb"] or rec["header_field_meaning"] != "style")
            result.append(row)

        return result

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]

        rows: list[list] = []
        for record in slice_:
            title_color = record["title_color_argb"]
            title_color_hex = title_color[4:] if title_color.startswith("0xFF") else ""

            rows.append([
                e(record["title_id"]),
                e(record["category"]),
                color_cell([title_color_hex]) if title_color_hex else "-",
                _title_cell(record["title"], record["title_color_css"]),
                e(record["requirement"]),
                e("True" if record["is_special"] else "False"),
                e(record["title_effect_name"] or "-"),
            ])

        return table(f"{len(records):,} titles decoded", self._columns(), rows)
