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

_OFFSET_FILE = "base_dialogoffset.dbss"
# Martina Finto's main dialog: dialog index 1 of character 40024.
_MARTINA_MAIN = 1 << 16 | 40024

BASE_CASE = HandlerCase(
    handler_name="base_dialog.dbss",
    data_file="base_dialog.dbss",
    companion_files={_OFFSET_FILE: _OFFSET_FILE},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Character", "Bubble Lines"],
    internal_path="gamecommondata/binary/base_dialog.dbss",
    tests=[
        SchemaTest(required_keys=["key", "character_id", "dialog_index", "character", "name_kr", "lines", "lines_kr", "line_count"]),
        DeclaredCountTest(declared=header_count(offset=0)),
        DeclaredCountTest(declared=header_count(offset=4, companion=_OFFSET_FILE)),
        RangeTest(col="character_id", min_val=0, max_val=0xFFFF),
        TargetTest(
            col="key",
            value=_MARTINA_MAIN,
            # LOC type 38 holds the dialog name and its lines in English.
            expected={
                "character_id": 40024,
                "dialog_index": 1,
                "character": "Martina Finto",
                "lines": [
                    "Oh David...\nMaybe I should open up a restaurant here at the farm...",
                    "He said I wouldn't have to lift a finger after I married him...",
                    "I should have listened to my sister...",
                ],
            },
        ),
    ],
)

OFFSET_CASE = HandlerCase(
    handler_name=_OFFSET_FILE,
    data_file=_OFFSET_FILE,
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path=f"gamecommondata/binary/{_OFFSET_FILE}",
    tests=[
        SchemaTest(required_keys=["key", "character_id", "dialog_index", "dbss_offset", "size"]),
        DeclaredCountTest(declared=header_count(offset=4)),
        TargetTest(col="key", value=_MARTINA_MAIN, expected={"character_id": 40024, "dialog_index": 1}),
    ],
)


@pytest.fixture(scope="module")
def base_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_BASE_RESULT", None)
    if result is None:
        result = run_case(replace(BASE_CASE, tests=[]))
        request.module._BASE_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", BASE_CASE.tests, ids=case_id)
def test_base_dialog_dbss(spec: Any, base_result: HandlerResult) -> None:
    base_result.check(spec)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_base_dialogoffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    offset_result.check(spec)
