"""Every handler with a fixture case stores an empty sort value behind each
cell it renders as a dash or blank, so those rows sort last ("Store none as
None" in docs/handler.md)."""
from __future__ import annotations

import html
import re

import pytest

from table_sort import is_empty
from tests.handler_cases import case_file_name, handler_cases
from tests.models import HandlerCase
from tests.runner import load_case

_HEADER_RE = re.compile(r"<th\b([^>]*)>")
_SORT_KEY_RE = re.compile(r'data-sort-key="([^"]+)"')
_ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
_CELL_RE = re.compile(r"<td\b[^>]*>(.*?)</td>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")
# Image cells (icons, sprite regions) have no text even when they show something.
_IMAGE_MARKERS = ("<img", "background")
_EMPTY_TEXTS = frozenset({"", "-"})
_MAX_REPORTED = 5


def _header_sort_keys(page: str) -> list[str | None]:
    """The sort key of each rendered column, None for an unsortable one."""
    head = page[page.index("<thead>") : page.index("</thead>")]
    keys: list[str | None] = []
    for attrs in _HEADER_RE.findall(head):
        match = _SORT_KEY_RE.search(attrs)
        keys.append(html.unescape(match.group(1)) if match else None)
    return keys


def _body_rows(page: str) -> list[list[str]]:
    body = page[page.index("<tbody>") :]
    return [_CELL_RE.findall(row) for row in _ROW_RE.findall(body)]


def _looks_empty(cell: str) -> bool:
    if any(marker in cell for marker in _IMAGE_MARKERS):
        return False
    return html.unescape(_TAG_RE.sub("", cell)).strip() in _EMPTY_TEXTS


def _shows_its_value(value: object, cell: str) -> bool:
    """True when the cell text is the value itself, like a name that is "-" in the game data."""
    return isinstance(value, str) and value.strip() == html.unescape(_TAG_RE.sub("", cell)).strip()


@pytest.mark.parametrize("case", handler_cases(), ids=case_file_name)
def test_empty_cells_sort_last(case: HandlerCase) -> None:
    loaded = load_case(case)
    handler = loaded.handler
    records = handler.get_records(loaded.data, loaded.entry, loaded.companions)
    if not records or "_error" in records[0]:
        pytest.skip("no parsed records")

    page = handler.render_records_page(records, 0, len(records))
    keys = _header_sort_keys(page)
    rows = _body_rows(page)
    assert len(rows) == len(records), "rendered rows do not match the records"

    mismatches: list[str] = []
    for record, cells in zip(records, rows):
        for key, cell in zip(keys, cells):
            if key is None or not _looks_empty(cell):
                continue
            value = record.get(key)
            if not is_empty(value) and not _shows_its_value(value, cell):
                mismatches.append(f"{key}={value!r}")

    assert not mismatches, (
        f"{len(mismatches)} empty cells sort by a value: {mismatches[:_MAX_REPORTED]}"
    )
