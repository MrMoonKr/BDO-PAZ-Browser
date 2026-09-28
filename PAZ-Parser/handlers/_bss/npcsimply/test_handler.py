from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import (
    DeclaredCountTest,
    HandlerCase,
    HandlerResult,
    RangeTest,
    SchemaTest,
    TargetTest,
    case_id,
    header_count,
    run_case,
)

from _dbss.characterspawntype.parser import ROLE_COUNT


# unknown_12 reads 0xFFFF on every row without an unknown_0c.
_NO_UNKNOWN_0C = 0xFFFF

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
                "unknown_0c",
                "unknown_10",
                "unknown_12",
                "unknown_14",
            ],
        ),
        DeclaredCountTest(declared=header_count(offset=4)),
        RangeTest(col="kind", min_val=0, max_val=ROLE_COUNT - 1),
        RangeTest(col="unknown_14", min_val=0, max_val=1),
        TargetTest(
            col="character_id",
            value=47791,
            expected={
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


def test_npcsimply_unknown_12_marks_rows_without_unknown_0c(npcsimply_result: HandlerResult) -> None:
    mismatched = [
        record["character_id"]
        for record in npcsimply_result.records
        if (record["unknown_12"] == _NO_UNKNOWN_0C) != (record["unknown_0c"] == 0)
    ]
    assert not mismatched, f"unknown_12 and unknown_0c disagree on characters {mismatched[:5]}"
