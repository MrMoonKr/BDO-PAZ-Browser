from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import (
    DeclaredCountTest,
    HandlerCase,
    HandlerResult,
    SchemaTest,
    TargetTest,
    case_id,
    header_count,
    run_case,
)


CASE = HandlerCase(
    handler_name="questgroup.dbss",
    data_file="questgroup.dbss",
    companion_files={},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Name", "Quest Titles"],
    internal_path="gamecommondata/binary/questgroup.dbss",
    tests=[
        SchemaTest(required_keys=["group_id", "name", "quest_count", "quest_titles", "quest_titles_text"]),
        DeclaredCountTest(declared=header_count()),
        # The first record follows the u32 count.
        TargetTest(col="row", value=0, expected={"offset": 0x4}),
        TargetTest(
            col="group_id",
            value=1022,
            expected={
                "name_kr": "소서러, 여정의 시작",
                "name": "Sorceress, Beginning of the Journey",
            },
        ),
        TargetTest(
            col="group_id",
            value=5801,
            expected={"name_kr": "거친 사막으로 달려가자!", "name": "To the Wild Desert!"},
        ),
    ],
)


@pytest.fixture(scope="module")
def questgroup_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_questgroup_dbss(spec: Any, questgroup_result: HandlerResult) -> None:
    questgroup_result.check(spec)
