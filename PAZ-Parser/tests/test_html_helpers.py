from __future__ import annotations

from api.bdo_api import _table_row_height
from _common.html import (
    flag_cell,
    icon_cell,
    icon_html_label_cell,
    icon_html_list_cell,
    icon_label_cell,
    icon_list_cell,
    sprite_icon_cell,
)


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


def test_icon_label_cell_shows_the_label_and_keeps_the_path_for_loading() -> None:
    html = icon_label_cell('ui/icon/a"b.dds', "Sap & <Knot>")

    assert 'class="icon-cell icon-label-cell"' in html
    assert 'data-icon-path="ui/icon/a&quot;b.dds"' in html
    assert '<span class="icon-cell-label">Sap &amp; &lt;Knot&gt;</span>' in html
    assert "icon-cell-path" not in html
    assert "icon-cell-placeholder" in html


def test_icon_label_cell_without_a_path_is_the_label_alone() -> None:
    assert icon_label_cell("", "Sap & Knot") == "Sap &amp; Knot"


def test_icon_list_cell_joins_entries_and_counts_the_hidden_ones() -> None:
    entries = [("ui/a.dds", "A"), ("", "B")]

    assert icon_list_cell(entries) == f"{icon_label_cell('ui/a.dds', 'A')}, B"
    assert icon_list_cell(entries, 3).endswith("B, ... (+3)")
    assert icon_list_cell([]) == ""


def test_icon_html_label_cell_keeps_the_label_markup() -> None:
    label = '<span class="pa-color">Sap</span>'

    assert f'<span class="icon-cell-label">{label}</span>' in icon_html_label_cell("ui/a.dds", label)
    assert icon_html_label_cell("", label) == label
    assert icon_html_label_cell("", label, tooltip="Buff 1") == f'<span title="Buff 1">{label}</span>'


def test_icon_html_list_cell_keeps_each_label_markup() -> None:
    entries = [("ui/a.dds", "<b>A</b>"), ("", "<b>B</b>")]

    assert icon_html_list_cell(entries) == f"{icon_html_label_cell('ui/a.dds', '<b>A</b>')}, <b>B</b>"
    assert icon_html_list_cell(entries, 2).endswith("<b>B</b>, ... (+2)")
