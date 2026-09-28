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
    handler_name="titleoffset.dbss",
    data_file="titleoffset.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/titleoffset.dbss",
    tests=[
        SchemaTest(required_keys=["title_id", "offset"]),
        DeclaredCountTest(declared=header_count()),
        # One title starts right after the u32 count of title.dbss.
        TargetTest(col="offset", value=0x4, expected={}),
    ],
)


@pytest.fixture(scope="module")
def titleoffset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_titleoffset_dbss(spec: Any, titleoffset_result: HandlerResult) -> None:
    titleoffset_result.check(spec)
