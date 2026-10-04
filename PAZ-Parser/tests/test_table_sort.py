"""Server-side table sort: ordering rules, handler hooks and sortable headers."""
from __future__ import annotations

import math

from bdo_models import PazEntry
from bdo_preview import PreviewHandler
from table_sort import TableSort, positions_in_order, sort_order
from _common.html import Column, sort_keys, table


def _values(records: list[dict], order: list[int], field: str = "v") -> list[object]:
    return [records[index][field] for index in order]


# ── sort_order ───────────────────────────────────────────────────────────────

def test_sort_order_numbers_ascending_and_descending() -> None:
    records = [{"v": 10}, {"v": 2}, {"v": 33}]

    assert _values(records, sort_order(records, "v", descending=False)) == [2, 10, 33]
    assert _values(records, sort_order(records, "v", descending=True)) == [33, 10, 2]


def test_sort_order_puts_empty_values_last_in_both_directions() -> None:
    records = [{"v": None}, {"v": 5}, {"v": ""}, {"v": 1}, {"v": []}, {"v": math.nan}]

    assert sort_order(records, "v", descending=False)[:2] == [3, 1]
    assert sort_order(records, "v", descending=True)[:2] == [1, 3]
    assert set(sort_order(records, "v", descending=True)[2:]) == {0, 2, 4, 5}


def test_sort_order_is_stable_for_equal_values() -> None:
    records = [{"v": 1, "id": "a"}, {"v": 0, "id": "b"}, {"v": 1, "id": "c"}]

    assert _values(records, sort_order(records, "v", descending=False), "id") == ["b", "a", "c"]
    assert _values(records, sort_order(records, "v", descending=True), "id") == ["a", "c", "b"]


def test_sort_order_text_ignores_case() -> None:
    records = [{"v": "beta"}, {"v": "Alpha"}, {"v": "gamma"}]

    assert _values(records, sort_order(records, "v", descending=False)) == ["Alpha", "beta", "gamma"]


def test_sort_order_mixed_column_ranks_numbers_before_text() -> None:
    records = [{"v": "x"}, {"v": 3}, {"v": True}, {"v": 2.5}]

    assert _values(records, sort_order(records, "v", descending=False)) == [True, 2.5, 3, "x"]


def test_sort_order_integer_column_is_stable_descending() -> None:
    records = [{"v": 2, "id": "a"}, {"v": 9, "id": "b"}, {"v": 2, "id": "c"}]

    assert _values(records, sort_order(records, "v", descending=True), "id") == ["b", "a", "c"]


def test_sort_order_text_column_folds_case_strips_and_puts_blanks_last() -> None:
    records = [{"v": "  "}, {"v": " beta"}, {"v": "ALPHA"}, {"v": ""}, {"v": "alpha"}]

    assert sort_order(records, "v", descending=False) == [2, 4, 1, 0, 3]
    assert sort_order(records, "v", descending=True) == [1, 2, 4, 0, 3]


def test_sort_order_missing_field_counts_as_empty() -> None:
    records = [{}, {"v": 1}]

    assert sort_order(records, "v", descending=False) == [1, 0]


def test_positions_in_order_maps_file_indices_to_sorted_positions() -> None:
    order = [2, 0, 1]  # record 2 shows first, record 0 second, record 1 third

    assert positions_in_order(order, [0, 1]) == [1, 2]
    assert positions_in_order(order, [1, 2]) == [0, 2]


def test_table_sort_parse_rejects_malformed_input() -> None:
    assert TableSort.parse("buff_id", "asc") == TableSort("buff_id", "asc")
    assert TableSort.parse("", "asc") is None
    assert TableSort.parse("buff_id", "up") is None
    assert TableSort.parse(None, "desc") is None


# ── PreviewHandler hooks ─────────────────────────────────────────────────────

class _NumberHandler(PreviewHandler):
    def __init__(self) -> None:
        self.get_records_call_count = 0

    def get_records(self, data: bytes, entry: PazEntry, companions: dict[str, bytes]) -> list[dict]:
        self.get_records_call_count += 1
        return [{"v": b} for b in data]

    def render_records_page(self, records: list[dict], page: int, page_size: int) -> str:
        start = page * page_size
        return ",".join(str(r["v"]) for r in records[start:start + page_size])


def _entry() -> PazEntry:
    return PazEntry(
        archive_name="test.paz",
        internal_path="foo.dbss",
        offset=0,
        compressed_size=4,
        uncompressed_size=4,
        compression_type=0,
        encryption_type=0,
    )


class _SortableNumberHandler(_NumberHandler):
    def sortable_fields(self) -> tuple[str, ...]:
        return ("v", "w")


def test_sortable_fields_default_is_empty() -> None:
    assert _NumberHandler().sortable_fields() == ()


def test_default_sort_is_none_without_sortable_fields() -> None:
    assert _NumberHandler().default_sort() is None


def test_default_sort_is_first_sortable_field_descending() -> None:
    assert _SortableNumberHandler().default_sort() == TableSort("v", "desc")


def test_render_sorted_page_sorts_across_all_pages() -> None:
    handler = _NumberHandler()
    data = bytes([40, 10, 30, 20])
    sort = TableSort("v", "desc")

    assert handler.render_sorted_page(data, _entry(), {}, 0, 2, sort) == "40,30"
    assert handler.render_sorted_page(data, _entry(), {}, 1, 2, sort) == "20,10"


def test_sorted_order_and_pages_parse_records_once() -> None:
    handler = _NumberHandler()
    data = bytes([40, 10, 30, 20])
    sort = TableSort("v", "asc")

    handler.render_sorted_page(data, _entry(), {}, 0, 2, sort)
    handler.render_sorted_page(data, _entry(), {}, 1, 2, TableSort("v", "desc"))
    assert list(handler.sorted_order(data, _entry(), {}, sort)) == [1, 3, 2, 0]
    assert handler.get_records_call_count == 1


# ── table() headers ──────────────────────────────────────────────────────────

def test_table_marks_only_columns_with_sort_key_sortable() -> None:
    html = table("meta", [Column("ID", "num", sort_key="buff_id"), Column("Icon")], [["1", "-"]])

    assert '<th class="num sortable" data-sort-key="buff_id" >ID</th>' in html
    assert '<th class="" >Icon</th>' in html


def test_table_plain_tuple_headers_are_not_sortable() -> None:
    html = table("meta", [("ID", "num", "")], [["1"]])

    assert "sortable" not in html
    assert '<td class="num">1</td>' in html


def test_sort_keys_collects_declared_fields_in_column_order() -> None:
    columns = [
        Column("Size", sort_key="size"),
        Column("Icon"),
        Column("ID", sort_key="buff_id"),
        Column("Size (raw)", sort_key="size"),
    ]

    assert sort_keys(columns) == ("size", "buff_id")
