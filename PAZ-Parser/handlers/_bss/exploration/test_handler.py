from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import (
    CountTest,
    HandlerCase,
    HandlerResult,
    PosTest,
    RangeTest,
    SchemaTest,
    TargetTest,
    case_id,
    run_case,
)


CASE = HandlerCase(
    handler_name="exploration.bss",
    data_file="exploration.bss",
    companion_files={},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Node Name"],
    internal_path="gamecommondata/binary/exploration.bss",
    tests=[
        SchemaTest(
            required_keys=[
                "node_key",
                "node_name",
                "name_kr",
                "node_kind",
                "kind",
                "enabled",
                "is_sub_node",
                "main_sub",
                "contribution",
                "manager_id",
                "manager",
                "representative_id",
                "representative",
                "radius",
                "knowledge_ids",
            ],
        ),
        CountTest(expected=1003),
        RangeTest(col="node_kind", min_val=0, max_val=15),
        RangeTest(col="contribution", min_val=0, max_val=3),
        # Named through LOC type 29. Type 34 (knowledge) gave "Cron Castle Altar".
        PosTest(
            pos=0,
            expected={
                "node_key": 65,
                "node_name": "Wale Farm",
                "name_kr": "웨일 농장",
                "kind": "Normal",
                "main_sub": "Main",
                "contribution": 1,
                "manager_id": 40605,
                "radius": 2700.0,
            },
        ),
        TargetTest(
            col="node_key",
            value=1,
            expected={
                "node_name": "Velia",
                "kind": "City",
                "contribution": 0,
                "manager": None,
                "representative_id": 40017,
                "radius": 12700.0,
            },
        ),
        TargetTest(
            col="node_key",
            value=3,
            expected={"node_name": "Cron Castle", "kind": "Dangerous", "contribution": 2},
        ),
    ],
)


@pytest.fixture(scope="module")
def exploration_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_exploration_bss(
    spec: Any,
    exploration_result: HandlerResult,
) -> None:
    spec.check(exploration_result.records)
