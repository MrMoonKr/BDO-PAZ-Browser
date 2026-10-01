from __future__ import annotations

import html as _html
import re
from collections.abc import Sequence
from typing import NamedTuple


class Column(NamedTuple):
    """One parsed-table column.

    ``sort_key`` names the raw record field the server sorts this column by
    (``duration_ms``, not the rendered ``1h 30m``). Columns without one render
    a plain, non-clickable header.
    """

    label: str
    css_class: str = ""
    extra_attrs: str = ""
    sort_key: str | None = None


def e(value: object) -> str:
    return _html.escape(str(value))


def truncate(text: str, max_len: int) -> str:
    """`text` cut to `max_len` characters plus an ellipsis, for long text cells."""
    return text if len(text) <= max_len else text[:max_len] + "…"


def join_limited(values: Sequence[str], max_items: int) -> str:
    """Comma-join the first `max_items` values and count the rest, for list cells."""
    if len(values) <= max_items:
        return ", ".join(values)
    return ", ".join(values[:max_items]) + f", ... (+{len(values) - max_items})"


def flag_cell(is_set: bool) -> str:
    """A yes/no cell: a green check mark or a red cross."""
    return '<span class="flag-yes">✓</span>' if is_set else '<span class="flag-no">✗</span>'


def color_cell(colors: list[str]) -> str:
    if not colors:
        return "-"

    parts: list[str] = []

    for color in colors:
        escaped_color = e(color)
        parts.append(
            f'<span class="color-swatch" style="background:#{escaped_color}"></span>'
            f'#{escaped_color}'
        )

    return " ".join(parts)


# The swatch an icon cell shows until the GUI (ui/js/features/table.js) or
# `browser.py --render` swaps in the image.
_ICON_PLACEHOLDER = '<span class="icon-cell-thumb icon-cell-placeholder" aria-hidden="true"></span>'

# An `icon_cell` still waiting for its image; group 1 is the escaped path.
PENDING_ICON_CELL_RE = re.compile(
    r'<span class="icon-cell" title="([^"]*)" data-icon-path="\1">'
    + re.escape(_ICON_PLACEHOLDER)
    + r'<span class="icon-cell-path">\1</span></span>'
)


def icon_cell(path: object, image_src: str | None = None) -> str:
    icon_path = str(path).strip()
    if not icon_path:
        return "-"

    escaped_path = e(icon_path)
    thumb = _ICON_PLACEHOLDER
    if image_src:
        thumb = f'<img class="icon-cell-thumb" src="{e(image_src)}" alt="" loading="lazy">'

    return (
        f'<span class="icon-cell" title="{escaped_path}" data-icon-path="{escaped_path}">'
        f'{thumb}'
        f'<span class="icon-cell-path">{escaped_path}</span>'
        f'</span>'
    )


# A sprite cell loads nothing: the sheet is shared by many rows and the sprite
# only shows in the icon popup a click opens (ui/js/features/icon-preview.js).
_SPRITE_PLACEHOLDER = '<span class="icon-cell-thumb sprite-cell-placeholder" aria-hidden="true"></span>'


def sprite_icon_cell(path: object, region: Sequence[int] | None) -> str:
    """An icon that is the (x1, y1, x2, y2) region of a sprite sheet; a dash without one."""
    sheet = str(path).strip()
    if not sheet or region is None or len(region) != 4:
        return "-"

    x1, y1, x2, y2 = (int(v) for v in region)
    escaped_sheet = e(sheet)
    title = e(f"{sheet} ({x1}, {y1}) to ({x2}, {y2})")
    return (
        f'<span class="icon-cell sprite-cell" title="{title}" data-sprite-path="{escaped_sheet}" '
        f'data-sprite-region="{x1},{y1},{x2},{y2}">'
        f'{_SPRITE_PLACEHOLDER}'
        f'<span class="icon-cell-path">{escaped_sheet}</span>'
        f'</span>'
    )


def missing_icon_cell(path: object) -> str:
    """An icon cell whose file the client does not ship: a dash, path in the tooltip.

    Matches what the GUI turns an unresolved `icon_cell` into.
    """
    escaped_path = e(str(path).strip())
    return (
        f'<span class="icon-cell icon-cell-missing" title="{escaped_path}" '
        f'data-icon-path="{escaped_path}">-</span>'
    )


def debug_cell(fields: dict[str, int], highlight_offset: int) -> str:
    parts: list[str] = []

    for name, value in fields.items():
        offset = int(name.split("_")[1], 16)
        css_class = "debug-field debug-field-hit" if offset == highlight_offset else "debug-field"
        parts.append(f'<span class="{css_class}">{e(name)}={e(value)}</span>')

    return " ".join(parts)


def sort_keys(columns: Sequence[Column]) -> frozenset[str]:
    """Record fields the given columns can be sorted by."""
    return frozenset(column.sort_key for column in columns if column.sort_key)


def header_cell(column: Column) -> str:
    """Render one `<th>`. Only columns with a sort key are clickable."""
    if not column.sort_key:
        return f'<th class="{column.css_class}" {column.extra_attrs}>{column.label}</th>'

    css_class = f"{column.css_class} sortable".strip()
    return (
        f'<th class="{css_class}" data-sort-key="{e(column.sort_key)}" {column.extra_attrs}>'
        f'{column.label}</th>'
    )


def table(
    meta: str,
    headers: Sequence[Column | tuple[str, str, str]],
    rows: list[list],
) -> str:
    """Render a parsed table. Plain ``(label, css_class, extra_attrs)`` tuples
    are accepted as unsortable columns."""
    columns = [header if isinstance(header, Column) else Column(*header) for header in headers]
    head = "".join(header_cell(column) for column in columns)

    body = "".join(
        "<tr>"
        + "".join(
            f'<td class="{columns[index].css_class}">{cell}</td>'
            for index, cell in enumerate(row)
        )
        + "</tr>"
        for row in rows
    )

    return (
        f'<div class="table-meta">{e(meta)}</div>'
        f'<div class="table-wrap">'
        f'<table class="data-table">'
        f'<thead><tr>{head}</tr></thead>'
        f'<tbody>{body}</tbody>'
        f'</table>'
        f'</div>'
    )


def error(text: str) -> str:
    return f'<div class="error">{e(text)}</div>'
