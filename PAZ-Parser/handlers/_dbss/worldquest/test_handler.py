from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import HandlerCase, HandlerResult, SchemaTest, TargetTest, case_id, run_case


CASE = HandlerCase(
    handler_name="worldquest.dbss",
    data_file="worldquest.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/worldquest.dbss",
    tests=[
        SchemaTest(required_keys=["count", "status", "extra_bytes"]),
        # The file is only its u32 count; the handler shows one status row for it.
        TargetTest(
            col="status",
            value="No world quest records",
            expected=[{"count": 0, "extra_bytes": 0}],
        ),
    ],
)


@pytest.fixture(scope="module")
def worldquest_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_worldquest_dbss(spec: Any, worldquest_result: HandlerResult) -> None:
    worldquest_result.check(spec)
