from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import (
    DeclaredCountTest,
    HandlerCase,
    HandlerResult,
    PaFieldTest,
    RangeTest,
    SchemaTest,
    TargetTest,
    case_id,
    header_count,
    run_case,
)


_TILE_DIR = "ui_texture/icon/new_icon/09_cash/03_product"
_DERIVED_DIR = "ui_texture/icon/new_icon/product_icon_png"

CASE = HandlerCase(
    handler_name="cashproduct.dbss",
    data_file="cashproduct.dbss",
    companion_files={"cashproductoffset.dbss": "cashproductoffset.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Product", "Item", "Description"],
    internal_path="gamecommondata/binary/cashproduct.dbss",
    tests=[
        SchemaTest(
            required_keys=[
                "product_id",
                "product_name",
                "product_icon_path",
                "item_id",
                "block_size",
                "item_name",
                "icon_path",
                "product",
                "description",
            ],
        ),
        PaFieldTest(field="product"),
        PaFieldTest(field="description"),
        DeclaredCountTest(declared=header_count()),
        RangeTest(col="item_id", min_val=0, max_val=0xFFFFFF),
        TargetTest(
            col="product_id",
            value=114415,
            expected={
                "product_icon_path": f"{_TILE_DIR}/00103985.dds",
                "item_id": 613110,
                # The displayed icon keys off the item, not the shop tile. No
                # index is installed under test, so this is the derived
                # fallback; the app resolves it through the item index.
                "icon_path": f"{_DERIVED_DIR}/00613110.png",
            },
        ),
        # Product ID, tile ID and item ID are three unrelated numbers; only this
        # file ties them together.
        TargetTest(
            col="product_id",
            value=117722,
            expected={
                "product_icon_path": f"{_TILE_DIR}/00105099.dds",
                "item_id": 340916,
                "item_name": "[Guardian] Shell Belle Outfit Set",
                "icon_path": f"{_DERIVED_DIR}/00340916.png",
            },
        ),
        # The product name comes from LOC type 50, not from the item: the item
        # is the bare pet, the product names its tier in colour.
        TargetTest(
            col="product_id",
            value=112655,
            expected={
                "product": "Polar Bear (Tier 3)",
                "_product_pa": "Polar Bear <PAColor0xffe9bd23>(Tier 3)<PAOldColor>",
            },
        ),
        # Rows under service code 12, which nearly every product uses, win over
        # the product's code 1 rows ("... (Used once per day)").
        TargetTest(
            col="product_id",
            value=21007,
            expected={"product": "[Loyalty] Unknown Dye Box"},
        ),
    ],
)


@pytest.fixture(scope="module")
def cashproduct_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_cashproduct_dbss(
    spec: Any,
    cashproduct_result: HandlerResult,
) -> None:
    cashproduct_result.check(spec)
