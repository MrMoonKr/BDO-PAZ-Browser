from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import CountTest, HandlerCase, HandlerResult, PosTest, SchemaTest, TargetTest, case_id, run_case


CASE = HandlerCase(
    handler_name="knowledgelearning.dbss",
    data_file="knowledgelearning.dbss",
    companion_files={"knowledgelearningoffset.dbss": "knowledgelearningoffset.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Knowledge Name"],
    internal_path="gamecommondata/binary/knowledgelearning.dbss",
    tests=[
        SchemaTest(required_keys=["table", "source_type", "source_id", "source_name", "card_id", "card_name"]),
        # Two tables: 2,533 characters, then 2,070 items.
        CountTest(expected=4603),
        PosTest(
            pos=0,
            expected={
                "table": 0,
                "source_type": "Character",
                "source_id": 10004,
                "source_name": "Feldspar",
                "card_id": 7302,
                "card_name": "Feldspar",
            },
        ),
        # The item table was misread before; its first row teaches the item's own card.
        TargetTest(
            col="source_id",
            value=4070,
            expected={
                "table": 1,
                "source_type": "Item",
                "source_name": "Processed Coal",
                "card_id": 7605,
                "card_name": "Processed Coal",
            },
        ),
    ],
)


@pytest.fixture(scope="module")
def knowledgelearning_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_knowledgelearning_dbss(spec: Any, knowledgelearning_result: HandlerResult) -> None:
    spec.check(knowledgelearning_result.records)
