from __future__ import annotations

import struct

import pytest

from tests.fixtures import load_binary_fixture

from _bss.menu.parser import build_menu_icon_index, build_menu_icon_region_index, parse_menu_records


_SHEET_DIR = "ui_texture/combine/icon/"


@pytest.fixture(scope="module")
def menu_data() -> bytes:
    return load_binary_fixture("menu.bss")


def test_one_record_per_declared_row(menu_data: bytes) -> None:
    (count,) = struct.unpack_from("<I", menu_data, 4)
    assert len(parse_menu_records(menu_data)) == count


def test_every_category_has_a_title_key_and_a_sprite(menu_data: bytes) -> None:
    records = parse_menu_records(menu_data)

    assert len({r["menu_id"] for r in records}) == len(records)
    for record in records:
        assert record["title_key"] and record["sheet"], record["menu_id"]
        assert record["icon_path"].startswith(_SHEET_DIR), record["menu_id"]
        x1, y1, x2, y2 = record["icon_region"]
        assert x2 > x1 and y2 > y1, record["menu_id"]


def test_icon_indexes_match_the_records(menu_data: bytes) -> None:
    records = parse_menu_records(menu_data)

    assert build_menu_icon_index(menu_data) == {r["menu_id"]: r["icon_path"] for r in records}
    assert build_menu_icon_region_index(menu_data) == {r["menu_id"]: r["icon_region"] for r in records}
