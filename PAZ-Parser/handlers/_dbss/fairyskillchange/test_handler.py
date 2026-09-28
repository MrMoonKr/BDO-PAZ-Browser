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
    fixed_rows,
    header_count,
    run_case,
)


_HEADER_SIZE = 4
_RECORD_SIZE = 12

CASE = HandlerCase(
    handler_name="fairyskillchange.dbss",
    data_file="fairyskillchange.dbss",
    companion_files={},
    loc_file="languagedata_en.loc",
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/fairyskillchange.dbss",
    tests=[
        SchemaTest(required_keys=["key", "level", "orb_cost"]),
        DeclaredCountTest(declared=header_count()),
        # The header count fills the file exactly.
        DeclaredCountTest(declared=fixed_rows(_RECORD_SIZE, header_size=_HEADER_SIZE)),
        # A reroll always costs at least one orb.
        RangeTest(col="orb_cost", min_val=1, max_val=float("inf")),
        # The record key is the level.
        TargetTest(col="level", value=1, expected={"key": 1}),
        TargetTest(col="level", value=50, expected={"key": 50}),
    ],
)

OFFSET_CASE = HandlerCase(
    handler_name="fairyskillchangeoffset.dbss",
    data_file="fairyskillchangeoffset.dbss",
    companion_files={},
    loc_file="languagedata_en.loc",
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/fairyskillchangeoffset.dbss",
    tests=[
        SchemaTest(required_keys=["level", "data_offset", "data_size", "record_start"]),
        DeclaredCountTest(declared=header_count()),
        DeclaredCountTest(declared=fixed_rows(_RECORD_SIZE, header_size=_HEADER_SIZE)),
        # Every payload is the 8 bytes trailing the 4-byte key prefix.
        RangeTest(col="data_size", min_val=8, max_val=8),
        # The first record follows the main file's u32 count.
        TargetTest(col="data_offset", value=8, expected={"record_start": 4}),
        TargetTest(col="level", value=1, expected={"data_size": 8}),
    ],
)


@pytest.fixture(scope="module")
def fairyskillchange_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.fixture(scope="module")
def fairyskillchangeoffset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_fairyskillchange_dbss(
    spec: Any,
    fairyskillchange_result: HandlerResult,
) -> None:
    fairyskillchange_result.check(spec)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_fairyskillchangeoffset_dbss(
    spec: Any,
    fairyskillchangeoffset_result: HandlerResult,
) -> None:
    fairyskillchangeoffset_result.check(spec)
