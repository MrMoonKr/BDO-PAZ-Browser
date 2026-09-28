from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import (
    CaseInput,
    DeclaredCount,
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


# Every record holds a baseline row plus ten level rows; the parser keeps the level rows.
_LEVEL_ROWS = 10


def _level_rows() -> DeclaredCount:
    """Level rows: the record count in the data file header, ten rows each."""
    records = header_count()

    def read(source: CaseInput) -> int:
        return records(source) * _LEVEL_ROWS

    return read


PETSKILL_CASE = HandlerCase(
    handler_name="petskill.dbss",
    data_file="petskill.dbss",
    companion_files={"petskilloffset.dbss": "petskilloffset.dbss"},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/petskill.dbss",
    tests=[
        SchemaTest(
            required_keys=[
                "pet_skill_id",
                "unknown_00",
                "level",
                "raw_value_a",
                "raw_value_b",
                "row_marker",
                "pet_skill_id_match",
            ]
        ),
        DeclaredCountTest(declared=_level_rows()),
        # The key prefix, the payload key and the offset row key agree.
        RangeTest(col="pet_skill_id_match", min_val=True, max_val=True),
        RangeTest(col="level", min_val=1, max_val=_LEVEL_ROWS),
        # The two record sizes: eleven 17-byte rows after the key, plus an optional trailing byte.
        RangeTest(col="data_size", min_val=189, max_val=190),
        TargetTest(
            col="pet_skill_id",
            value=47,
            expected=[{"level": level} for level in range(1, _LEVEL_ROWS + 1)],
        ),
        TargetTest(col="pet_skill_id", value=1, expected={"level": 1}),
    ],
)

PETSKILL_OFFSET_CASE = HandlerCase(
    handler_name="petskilloffset.dbss",
    data_file="petskilloffset.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/petskilloffset.dbss",
    tests=[
        SchemaTest(required_keys=["pet_skill_id", "data_offset", "data_size", "record_start"]),
        DeclaredCountTest(declared=header_count()),
        RangeTest(col="data_size", min_val=189, max_val=190),
        RangeTest(col="padding", min_val=0, max_val=0),
    ],
)


@pytest.fixture(scope="module")
def petskill_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_PETSKILL_RESULT", None)
    if result is None:
        result = run_case(replace(PETSKILL_CASE, tests=[]))
        request.module._PETSKILL_RESULT = result
    return result


@pytest.fixture(scope="module")
def petskill_offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_PETSKILL_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(PETSKILL_OFFSET_CASE, tests=[]))
        request.module._PETSKILL_OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", PETSKILL_CASE.tests, ids=case_id)
def test_petskill_dbss(spec: Any, petskill_result: HandlerResult) -> None:
    petskill_result.check(spec)


@pytest.mark.parametrize("spec", PETSKILL_OFFSET_CASE.tests, ids=case_id)
def test_petskilloffset_dbss(spec: Any, petskill_offset_result: HandlerResult) -> None:
    petskill_offset_result.check(spec)
