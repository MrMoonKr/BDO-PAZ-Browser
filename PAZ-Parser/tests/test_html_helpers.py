from __future__ import annotations

from api.bdo_api import _table_row_height
from _common.html import flag_cell, icon_cell, sprite_icon_cell


def test_icon_cell_renders_escaped_icon_path() -> None:
    html = icon_cell('Icon/Quest/Hadum08"><.dds')

    assert 'class="icon-cell"' in html
    assert 'Icon/Quest/Hadum08&quot;&gt;&lt;.dds' in html
    assert 'data-icon-path="Icon/Quest/Hadum08&quot;&gt;&lt;.dds"' in html
    assert 'icon-cell-placeholder' in html


def test_icon_cell_renders_empty_path_as_dash() -> None:
    assert icon_cell("") == "-"


def test_table_row_height_clamps_to_supported_range() -> None:
    assert _table_row_height("bad") == 27
    assert _table_row_height(10) == 20
    assert _table_row_height(80) == 64
    assert _table_row_height(32) == 32


def test_sprite_icon_cell_carries_the_sheet_and_region() -> None:
    html = sprite_icon_cell("ui_texture/combine/icon/a&b.dds", (2, 457, 57, 512))

    assert 'data-sprite-path="ui_texture/combine/icon/a&amp;b.dds"' in html
    assert 'data-sprite-region="2,457,57,512"' in html
    assert "sprite-cell-placeholder" in html
    assert "<img" not in html


def test_sprite_icon_cell_without_a_sheet_or_region_is_a_dash() -> None:
    assert sprite_icon_cell("", (0, 0, 1, 1)) == "-"
    assert sprite_icon_cell("ui_texture/a.dds", None) == "-"


def test_flag_cell_marks_set_and_unset() -> None:
    assert flag_cell(True) == '<span class="flag-yes">✓</span>'
    assert flag_cell(False) == '<span class="flag-no">✗</span>'
