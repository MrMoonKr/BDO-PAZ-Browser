"""Every handler with a fixture case renders sortable headers and sorts by each of them."""
from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

from table_sort import SORT_ASC, SORT_DESC, TableSort
from tests.models import HandlerCase
from tests.runner import LoadedCase, load_case

_HANDLERS_DIR = Path(__file__).resolve().parent.parent / "handlers"
_SORT_KEY_RE = re.compile(r'data-sort-key="([^"]+)"')
_PAGE_SIZE = 50


def _handler_cases() -> list[HandlerCase]:
    """Every module-level HandlerCase in the handler-local test modules."""
    cases: dict[str, HandlerCase] = {}
    for path in sorted(_HANDLERS_DIR.glob("*/*/test_*.py")):
        module_name = ".".join(path.relative_to(_HANDLERS_DIR).with_suffix("").parts)
        module = importlib.import_module(module_name)
        for value in vars(module).values():
            if isinstance(value, HandlerCase):
                cases.setdefault(value.internal_path, value)
    return list(cases.values())


def _assert_headers_are_declared(loaded: LoadedCase) -> None:
    fields = loaded.handler.sortable_fields()
    html = loaded.handler.render_data_page(loaded.data, loaded.entry, loaded.companions, 0, _PAGE_SIZE)
    rendered = set(_SORT_KEY_RE.findall(html))

    assert fields, "handler declares no sortable fields"
    assert rendered, "first page renders no sortable headers"
    # Handlers may declare fields for columns hidden on this page (LOC names,
    # inactive flags) so a saved sort survives, but never render undeclared ones.
    assert rendered <= fields


def _assert_sorts_every_field(loaded: LoadedCase) -> None:
    handler = loaded.handler
    count = handler.get_record_count(loaded.data, loaded.entry, loaded.companions)

    for field in sorted(handler.sortable_fields()):
        for direction in (SORT_ASC, SORT_DESC):
            sort = TableSort(field, direction)
            order = handler.sorted_order(loaded.data, loaded.entry, loaded.companions, sort)
            assert sorted(order) == list(range(count)), f"{sort} is not a permutation"

            html = handler.render_sorted_page(
                loaded.data, loaded.entry, loaded.companions, 0, _PAGE_SIZE, sort
            )
            assert "<tr>" in html, f"{sort} rendered no rows"


@pytest.mark.parametrize("case", _handler_cases(), ids=lambda case: Path(case.internal_path).name)
def test_handler_sorts_by_every_rendered_column(case: HandlerCase) -> None:
    loaded = load_case(case)

    _assert_headers_are_declared(loaded)
    _assert_sorts_every_field(loaded)
