from __future__ import annotations

from collections.abc import Iterator

import pytest

from _common.html import e, truncate
from _common.pa_text import (
    argb_css,
    pa_cell,
    pa_fields,
    pa_html,
    pa_key,
    set_show_pa_tags,
    strip_pa_tags,
)

_GOLD = "rgba(233, 189, 35, 1)"
_GOLD_OPEN = f'<span class="pa-color" style="color: {_GOLD}">'
_BOON = "<PAColor0xffe9bd23>[Blessing] Adventure's Boon<PAOldColor>\nAll AP +8"

_SAMPLES = [
    "",
    "Plain text",
    _BOON,
    "<PAColor0xffe9bd23>a <PAColor0xff00ff00>b<PAOldColor> c<PAOldColor>",
    "<PAColor0xffe9bd23>unclosed",
    "stray<PAOldColor> close",
    "<PAFoo>unknown",
    "<PAColor0xffe9bd23>\"Q\" & <A><PAOldColor> 'x'",
]


def test_plain_text_is_escaped_only() -> None:
    assert pa_html("Plain text") == "Plain text"
    assert pa_html("") == ""


def test_one_colour_becomes_a_span() -> None:
    assert pa_html("<PAColor0xffe9bd23>gold<PAOldColor>") == f"{_GOLD_OPEN}gold</span>"


def test_adventures_boon_title_is_gold() -> None:
    html = pa_html(_BOON)

    assert html == f"{_GOLD_OPEN}[Blessing] Adventure&#x27;s Boon</span>\nAll AP +8"


def test_nested_colours_close_in_order() -> None:
    html = pa_html("<PAColor0xffe9bd23>a <PAColor0xff00ff00>b<PAOldColor> c<PAOldColor>")

    green_open = '<span class="pa-color" style="color: rgba(0, 255, 0, 1)">'
    assert html == f"{_GOLD_OPEN}a {green_open}b</span> c</span>"


def test_unclosed_colour_is_closed_at_the_end() -> None:
    assert pa_html("<PAColor0xffe9bd23>open") == f"{_GOLD_OPEN}open</span>"


def test_stray_old_color_is_dropped() -> None:
    assert pa_html("a<PAOldColor>b") == "ab"


def test_non_opaque_alpha_is_kept() -> None:
    html = pa_html("<PAColor0xaa112233>x<PAOldColor>")

    assert 'style="color: rgba(17, 34, 51, 0.667)"' in html


def test_unknown_pa_tag_is_dropped() -> None:
    assert pa_html("<PAFoo>a<PABar 1>b") == "ab"


def test_malformed_colour_opens_an_unstyled_level() -> None:
    html = pa_html("<PAColor0xffe9bd23>a<PAColor0xzz>b<PAOldColor>c<PAOldColor>")

    assert html == f'{_GOLD_OPEN}a<span class="pa-color">b</span>c</span>'


def test_markup_and_quotes_are_escaped_with_colours() -> None:
    html = pa_html("<PAColor0xffe9bd23>\"Q\" & <A><PAOldColor> 'x'")

    assert html == f"{_GOLD_OPEN}&quot;Q&quot; &amp; &lt;A&gt;</span> &#x27;x&#x27;"


def test_markup_and_quotes_are_escaped_without_colours() -> None:
    html = pa_html("<PAColor0xffe9bd23>\"Q\" & <A><PAOldColor> 'x'", colors=False)

    assert html == "&quot;Q&quot; &amp; &lt;A&gt; &#x27;x&#x27;"


@pytest.mark.parametrize("raw", _SAMPLES)
def test_colours_off_equals_escaped_plain_text(raw: str) -> None:
    assert pa_html(raw, colors=False) == e(strip_pa_tags(raw))


@pytest.mark.parametrize("raw", _SAMPLES)
def test_spans_always_balance(raw: str) -> None:
    html = pa_html(raw)

    assert html.count("<span") == html.count("</span>")


@pytest.fixture
def shown_tags() -> Iterator[None]:
    set_show_pa_tags(True)
    try:
        yield
    finally:
        set_show_pa_tags(False)


@pytest.mark.usefixtures("shown_tags")
def test_shown_tags_stay_visible_outside_the_colour() -> None:
    html = pa_html("<PAColor0xffe9bd23>gold<PAOldColor>")

    assert html == (
        '<span class="pa-tag">&lt;PAColor0xffe9bd23&gt;</span>'
        f"{_GOLD_OPEN}gold</span>"
        '<span class="pa-tag">&lt;PAOldColor&gt;</span>'
    )


@pytest.mark.usefixtures("shown_tags")
def test_shown_tags_keep_stray_and_unknown_tags() -> None:
    html = pa_html("a<PAOldColor><PAFoo>b")

    assert html == (
        'a<span class="pa-tag">&lt;PAOldColor&gt;</span>'
        '<span class="pa-tag">&lt;PAFoo&gt;</span>b'
    )


@pytest.mark.usefixtures("shown_tags")
def test_shown_tags_without_colours_keep_only_the_tags() -> None:
    html = pa_html("<PAColor0xffe9bd23>gold<PAOldColor>", colors=False)

    assert html == (
        '<span class="pa-tag">&lt;PAColor0xffe9bd23&gt;</span>'
        "gold"
        '<span class="pa-tag">&lt;PAOldColor&gt;</span>'
    )


def test_strip_pa_tags_keeps_whitespace() -> None:
    assert strip_pa_tags(_BOON) == "[Blessing] Adventure's Boon\nAll AP +8"


def test_argb_css_opaque() -> None:
    assert argb_css(0xFFE9BD23) == _GOLD


def test_argb_css_partly_transparent() -> None:
    assert argb_css(0xF0FFFFFF) == "rgba(255, 255, 255, 0.941)"
    assert argb_css(0x00000000) == "rgba(0, 0, 0, 0)"


@pytest.mark.parametrize("value", [-1, 0x1_0000_0000, True])
def test_argb_css_rejects_values_out_of_range(value: int) -> None:
    with pytest.raises(ValueError):
        argb_css(value)


def test_pa_fields_keep_plain_and_tagged_text() -> None:
    fields = pa_fields("title", " <PAColor0xffe9bd23>Boon<PAOldColor> ")

    assert fields == {"title": "Boon", "_title_pa": " <PAColor0xffe9bd23>Boon<PAOldColor> "}
    assert pa_key("title") == "_title_pa"


def test_pa_cell_draws_the_tagged_copy() -> None:
    record = pa_fields("title", "<PAColor0xffe9bd23>Boon<PAOldColor>")

    assert pa_cell(record, "title") == f"{_GOLD_OPEN}Boon</span>"


def test_pa_cell_of_blank_text_is_a_dash() -> None:
    assert pa_cell(pa_fields("title", "<PAColor0xffe9bd23> <PAOldColor>"), "title") == "-"


def test_max_chars_cuts_inside_a_colour_and_closes_it() -> None:
    html = pa_html("<PAColor0xffe9bd23>golden<PAOldColor> tail", max_chars=3)

    assert html == f"{_GOLD_OPEN}gol…</span>"


def test_max_chars_leaves_short_text_whole() -> None:
    assert pa_html("<PAColor0xffe9bd23>gold<PAOldColor>", max_chars=4) == f"{_GOLD_OPEN}gold</span>"


@pytest.mark.parametrize("raw", _SAMPLES)
@pytest.mark.parametrize("max_chars", [0, 1, 3, 5, 12])
def test_max_chars_matches_truncate_on_plain_text(raw: str, max_chars: int) -> None:
    expected = e(truncate(strip_pa_tags(raw), max_chars))

    assert pa_html(raw, colors=False, max_chars=max_chars) == expected
    assert pa_html(raw, max_chars=max_chars).count("<span") == pa_html(raw, max_chars=max_chars).count("</span>")
