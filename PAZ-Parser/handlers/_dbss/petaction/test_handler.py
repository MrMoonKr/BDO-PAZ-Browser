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
    UserLanguageTest,
    case_id,
    header_count,
    run_case,
)


_OFFSET_FILE = "petactionoffset.dbss"

PETACTION_CASE = HandlerCase(
    handler_name="petaction.dbss",
    data_file="petaction.dbss",
    companion_files={_OFFSET_FILE: _OFFSET_FILE},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["action_name"],
    internal_path="gamecommondata/binary/petaction.dbss",
    tests=[
        SchemaTest(
            required_keys=[
                "action_id",
                "action_name",
                "icon_action_name",
                "name_kr",
                "icon_path",
                "record_offset",
                "record_size",
                "trailing_zeroes",
                "action_id_match",
            ]
        ),
        # The data file has no count; the offset table declares it.
        DeclaredCountTest(declared=header_count(companion=_OFFSET_FILE)),
        RangeTest(col="action_id_match", min_val=True, max_val=True),
        RangeTest(col="trailing_zeroes", min_val=True, max_val=True),
        # LOC type 19 names every action, so the Korean fallback never shows.
        UserLanguageTest(fields=["action_name"]),
        TargetTest(
            col="action_id",
            value=0,
            expected={
                "action_name": "Joy",
                "icon_action_name": "Like",
                "name_kr": "기쁨",
                "icon_path": "New_Icon/08_Servant_Skill/02_Pet/Action_0_Like.dds",
            },
        ),
        # The one four-character Korean name; it was once read as a second hash.
        TargetTest(
            col="action_id",
            value=7,
            expected={
                "action_name": "Crouch",
                "icon_action_name": "Play2",
                "name_kr": "웅크리기",
                "icon_path": "New_Icon/08_Servant_Skill/02_Pet/Action_7_Play2.dds",
            },
        ),
    ],
)

OFFSET_CASE = HandlerCase(
    handler_name="petactionoffset.dbss",
    data_file="petactionoffset.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/petactionoffset.dbss",
    tests=[
        SchemaTest(required_keys=["action_id", "record_offset", "record_size"]),
        DeclaredCountTest(declared=header_count()),
        # The data file has no header, so action 0 starts at byte 0.
        TargetTest(col="action_id", value=0, expected={"record_offset": 0}),
    ],
)


@pytest.fixture(scope="module")
def petaction_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_PETACTION_RESULT", None)
    if result is None:
        result = run_case(replace(PETACTION_CASE, tests=[]))
        request.module._PETACTION_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", PETACTION_CASE.tests, ids=case_id)
def test_petaction_dbss(spec: Any, petaction_result: HandlerResult) -> None:
    petaction_result.check(spec)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_petactionoffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    offset_result.check(spec)
