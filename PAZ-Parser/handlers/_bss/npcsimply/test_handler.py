from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import (
    CountTest,
    HandlerCase,
    HandlerResult,
    PosTest,
    RangeTest,
    SchemaTest,
    TargetTest,
    case_id,
    run_case,
)


CASE = HandlerCase(
    handler_name="npcsimply.bss",
    data_file="npcsimply.bss",
    companion_files={},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Name (EN)"],
    internal_path="gamecommondata/binary/npcsimply.bss",
    tests=[
        SchemaTest(
            required_keys=[
                "character_id",
                "name",
                "kind",
                "kind_name",
                "name_kr",
                "role_kr",
                "script",
                "knowledge_id",
                "unknown_02",
                "unknown_id",
                "unknown_value",
                "sentinel",
                "unknown_flag",
            ],
        ),
        CountTest(expected=2237),
        RangeTest(col="kind", min_val=1, max_val=40),
        PosTest(
            pos=0,
            expected={
                "character_id": 47791,
                "unknown_02": 53,
                "kind": 4,
                "kind_name": "ImportantNpc",
                "name_kr": "에론",
                "role_kr": "<거점 관리인>",
                "script": "getknowledge(15936);",
                "knowledge_id": 15936,
            },
        ),
        # No action script: the empty pool string, so no knowledge ID.
        TargetTest(
            col="character_id",
            value=47727,
            expected={
                "name": "Jackson",
                "kind_name": "ShopMerchant",
                "name_kr": "잭슨",
                "role_kr": "<과일상인>",
                "script": "",
                "knowledge_id": None,
            },
        ),
        TargetTest(
            col="character_id",
            value=47647,
            expected={
                "name": "Neoksam",
                "kind": 25,
                "kind_name": "ItemMarket",
                "role_kr": "<거래소장>",
                "knowledge_id": 2387,
            },
        ),
        # One of the 58 rows with an extra ID and value.
        TargetTest(
            col="character_id",
            value=47008,
            expected={
                "kind_name": "ShopMerchant",
                "knowledge_id": 1342,
                "unknown_id": 3001,
                "unknown_value": 10,
                "sentinel": 0,
                "unknown_flag": 1,
            },
        ),
        # The only script spelled `getKnowledge`.
        TargetTest(
            col="character_id",
            value=50613,
            expected={"script": "getKnowledge(933);", "knowledge_id": 933},
        ),
    ],
)


@pytest.fixture(scope="module")
def npcsimply_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_npcsimply_bss(spec: Any, npcsimply_result: HandlerResult) -> None:
    npcsimply_result.check(spec)
