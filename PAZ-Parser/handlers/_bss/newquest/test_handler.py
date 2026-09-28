from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import (
    HandlerCase,
    HandlerResult,
    RangeTest,
    SchemaTest,
    TargetTest,
    case_id,
    header_count,
    run_case,
)


CASE = HandlerCase(
    handler_name="newquest.bss",
    data_file="newquest.bss",
    companion_files={},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Title"],
    internal_path="gamecommondata/binary/newquest.bss",
    tests=[
        SchemaTest(
            required_keys=[
                "group",
                "row",
                "unknown_00",
                "quest_chain_id",
                "quest_id",
                "packed_quest_id",
                "title",
                "unknown_05",
                "unknown_09",
                "unknown_0d",
            ],
        ),
        # Zero in every row; a row read off its 17-byte stride would not be.
        RangeTest(col="unknown_00", min_val=0, max_val=0),
        TargetTest(
            col="packed_quest_id",
            value=600883,
            expected={
                "quest_chain_id": 11059,
                "quest_id": 9,
                "title": "[Event] Love for Pets",
            },
        ),
        TargetTest(
            col="packed_quest_id",
            value=77129,
            expected={"quest_chain_id": 11593, "quest_id": 1},
        ),
    ],
)


@pytest.fixture(scope="module")
def newquest_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_newquest_bss(spec: Any, newquest_result: HandlerResult) -> None:
    newquest_result.check(spec)


def test_newquest_bss_reaches_last_group(newquest_result: HandlerResult) -> None:
    # The file declares only a group count; each group header holds its own row count.
    group_count = header_count(offset=4)(newquest_result.source)

    assert max(record["group"] for record in newquest_result.records) == group_count - 1
