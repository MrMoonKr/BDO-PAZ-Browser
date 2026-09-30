from __future__ import annotations

from collections import Counter

import pytest

from tests.fixtures import load_binary_fixture

from _bss.menu.parser import parse_menu_records
from _bss.submenu.parser import (
    build_submenu_icon_index,
    build_submenu_icon_region_index,
    parse_submenu_records,
)


_SHEET_DIR = "ui_texture/combine/icon/"


@pytest.fixture(scope="module")
def submenu_data() -> bytes:
    return load_binary_fixture("submenu.bss")


@pytest.fixture(scope="module")
def menu_data() -> bytes:
    return load_binary_fixture("menu.bss")


def test_every_entry_belongs_to_a_menu_category(submenu_data: bytes, menu_data: bytes) -> None:
    menu_ids = {r["menu_id"] for r in parse_menu_records(menu_data)}

    assert all(r["menu_id"] in menu_ids for r in parse_submenu_records(submenu_data))


def test_entry_counts_match_the_menu_rows(submenu_data: bytes, menu_data: bytes) -> None:
    per_menu = Counter(r["menu_id"] for r in parse_submenu_records(submenu_data))

    for menu in parse_menu_records(menu_data):
        assert per_menu[menu["menu_id"]] == menu["submenu_count"], menu["menu_id"]


def test_every_entry_has_a_title_key_and_a_sprite(submenu_data: bytes) -> None:
    records = parse_submenu_records(submenu_data)

    assert len({r["entry_id"] for r in records}) == len(records)
    for record in records:
        assert record["title_key"] and record["sheet"], record["entry_id"]
        assert record["icon_path"].startswith(_SHEET_DIR), record["entry_id"]
        x1, y1, x2, y2 = record["icon_region"]
        assert x2 > x1 and y2 > y1, record["entry_id"]


def test_icon_indexes_match_the_records(submenu_data: bytes) -> None:
    records = parse_submenu_records(submenu_data)

    assert build_submenu_icon_index(submenu_data) == {r["entry_id"]: r["icon_path"] for r in records}
    assert build_submenu_icon_region_index(submenu_data) == {
        r["entry_id"]: r["icon_region"] for r in records
    }
