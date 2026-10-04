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


CASE = HandlerCase(
    handler_name="zodiacsignindex.bss",
    data_file="zodiacsignindex.bss",
    companion_files={"zodiacsign.dbss": "zodiacsign.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Name"],
    internal_path="gamecommondata/customization/zodiacsignindex.bss",
    tests=[
        SchemaTest(required_keys=["slot", "zodiac_id", "name", "known"]),
        DeclaredCountTest(declared=header_count(offset=4)),
        # Every listed ID is a sign in zodiacsign.dbss.
        RangeTest(col="known", min_val=True, max_val=True),
        UserLanguageTest(fields=["name"]),
        TargetTest(col="zodiac_id", value=1, expected={"name": "Hammer"}),
        TargetTest(col="zodiac_id", value=12, expected={"name": "Goblin"}),
    ],
)


@pytest.fixture(scope="module")
def zodiacsignindex_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_zodiacsignindex_bss(spec: Any, zodiacsignindex_result: HandlerResult) -> None:
    zodiacsignindex_result.check(spec)
