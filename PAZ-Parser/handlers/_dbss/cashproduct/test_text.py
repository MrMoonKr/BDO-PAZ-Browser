"""Pearl Shop texts from LOC type 50: which service code a product's text comes from."""
from __future__ import annotations

from types import MappingProxyType

import pytest

from _dbss.cashproduct import text
from _dbss.cashproduct.text import LOC_CASH_PRODUCT, ProductText, product_texts

_NAME = 0
_DESCRIPTION = 3


def _use_loc(monkeypatch: pytest.MonkeyPatch, rows: dict[tuple[int, int, int], str]) -> None:
    """LOC type 50 holding `rows`, keyed (product ID, service code, field)."""
    entries = {
        (LOC_CASH_PRODUCT, product_id, 0, code, field): value
        for (product_id, code, field), value in rows.items()
    }
    monkeypatch.setattr(text, "loc_type_entries", lambda str_type: MappingProxyType(entries))


def test_the_code_most_products_use_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_loc(monkeypatch, {
        (1, 12, _NAME): "Dye Box",
        (1, 1, _NAME): "Dye Box (Used once per day)",
        (2, 12, _NAME): "Gloves",
        (2, 12, _DESCRIPTION): "<PAColor0xffe9bd23>Contains<PAOldColor>",
    })

    assert product_texts() == {
        1: ProductText(name="Dye Box", description=""),
        2: ProductText(name="Gloves", description="<PAColor0xffe9bd23>Contains<PAOldColor>"),
    }


def test_a_product_without_the_main_code_takes_its_lowest(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_loc(monkeypatch, {
        (1, 12, _NAME): "Gloves",
        (2, 12, _NAME): "Armor",
        (3, 28, _NAME): "Helmet (28)",
        (3, 26, _NAME): "Helmet (26)",
    })

    assert product_texts()[3].name == "Helmet (26)"


def test_empty_without_loc(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_loc(monkeypatch, {})

    assert product_texts() == {}
