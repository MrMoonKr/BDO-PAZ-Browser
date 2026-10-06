from __future__ import annotations

import struct
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
    run_case,
)


_OFFSET_FILE = "fitnessleveloffset.dbss"
_LEVEL_ROW_SIZE = 29
_OFFSET_ROW_SIZE = 12
_U32 = struct.Struct("<I")
# Breath, Strength and Health.
_FITNESS_TYPES = (0, 1, 2)


def _block_rows(row_size: int, *, has_type_count: bool, companion: str | None = None) -> DeclaredCount:
    """Rows the u32 block counts declare, checking the blocks fill the file exactly."""

    def read(source: CaseInput) -> int:
        raw = source.file(companion)
        cursor = _U32.size if has_type_count else 0
        total = 0
        while cursor < len(raw):
            (count,) = _U32.unpack_from(raw, cursor)
            cursor += _U32.size + count * row_size
            total += count
        if cursor != len(raw):
            raise AssertionError(f"blocks end at {cursor}, file holds {len(raw)} bytes")
        return total

    return read


CASE = HandlerCase(
    handler_name="fitnesslevel.dbss",
    data_file="fitnesslevel.dbss",
    companion_files={_OFFSET_FILE: _OFFSET_FILE},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/fitnesslevel.dbss",
    tests=[
        SchemaTest(
            required_keys=[
                "fitness_type",
                "fitness_name",
                "level",
                "exp",
                "max_stamina",
                "weight_limit",
                "max_hp",
                "max_mp",
            ]
        ),
        DeclaredCountTest(declared=_block_rows(_LEVEL_ROW_SIZE, has_type_count=True)),
        DeclaredCountTest(declared=_block_rows(_OFFSET_ROW_SIZE, has_type_count=False, companion=_OFFSET_FILE)),
        RangeTest(col="fitness_type", min_val=min(_FITNESS_TYPES), max_val=max(_FITNESS_TYPES)),
        RangeTest(col="exp", min_val=0, max_val=2**64 - 1),
        TargetTest(col="fitness_type", value=0, expected={"fitness_name": "Breath"}),
        TargetTest(col="fitness_type", value=1, expected={"fitness_name": "Strength"}),
        TargetTest(col="fitness_type", value=2, expected={"fitness_name": "Health"}),
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
        SchemaTest(required_keys=["fitness_type", "level", "data_offset", "data_size"]),
        DeclaredCountTest(declared=_block_rows(_OFFSET_ROW_SIZE, has_type_count=False)),
        RangeTest(col="data_size", min_val=_LEVEL_ROW_SIZE, max_val=_LEVEL_ROW_SIZE),
        # The first Breath row follows the data file's type count and level count.
        TargetTest(col="fitness_type", value=0, expected={"level": 0, "data_offset": 8}),
    ],
)


@pytest.fixture(scope="module")
def fitnesslevel_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_FITNESSLEVEL_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._FITNESSLEVEL_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_fitnesslevel_dbss(spec: Any, fitnesslevel_result: HandlerResult) -> None:
    fitnesslevel_result.check(spec)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_fitnessleveloffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    offset_result.check(spec)
