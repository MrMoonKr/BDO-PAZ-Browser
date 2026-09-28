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
    header_count,
    run_case,
)


_OFFSET_FILE = "petexpoffset.dbss"
_OFFSET_HEADER_SIZE = 4
_OFFSET_ROW_SIZE = 10
# Every payload holds 50 u64 thresholds, populated up to its max_level.
_LEVEL_CAPACITY = 50
_PAYLOAD_SIZE = 2 + 4 + _LEVEL_CAPACITY * 8


def _level_rows() -> DeclaredCount:
    """Level rows: the max_level each offset row's payload declares, summed."""

    def read(source: CaseInput) -> int:
        offsets = source.file(_OFFSET_FILE)
        data = source.file(None)
        (count,) = struct.unpack_from("<I", offsets, 0)
        total = 0
        for index in range(count):
            (data_offset,) = struct.unpack_from("<I", offsets, _OFFSET_HEADER_SIZE + index * _OFFSET_ROW_SIZE + 2)
            (max_level,) = struct.unpack_from("<I", data, data_offset + 2)
            total += max_level
        return total

    return read


PETEXP_CASE = HandlerCase(
    handler_name="petexp.dbss",
    data_file="petexp.dbss",
    companion_files={_OFFSET_FILE: _OFFSET_FILE},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/petexp.dbss",
    tests=[
        SchemaTest(
            required_keys=[
                "exp_table_id",
                "prefix_exp_table_id",
                "offset_exp_table_id",
                "key_match",
                "max_level",
                "level",
                "required_exp",
                "data_offset",
                "data_size",
            ]
        ),
        DeclaredCountTest(declared=_level_rows()),
        # The key prefix, the payload key and the offset row key agree.
        RangeTest(col="key_match", min_val=True, max_val=True),
        RangeTest(col="max_level", min_val=1, max_val=_LEVEL_CAPACITY),
        RangeTest(col="level", min_val=1, max_val=_LEVEL_CAPACITY),
        # Populated thresholds are non-zero; unused slots are zero-filled.
        RangeTest(col="required_exp", min_val=1, max_val=2**64 - 1),
        TargetTest(col="exp_table_id", value=9, expected={"level": 1}),
        TargetTest(col="exp_table_id", value=1, expected={"level": 1}),
    ],
)

OFFSET_CASE = HandlerCase(
    handler_name="petexpoffset.dbss",
    data_file="petexpoffset.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/petexpoffset.dbss",
    tests=[
        SchemaTest(required_keys=["exp_table_id", "data_offset", "data_size", "record_start"]),
        DeclaredCountTest(declared=header_count()),
        RangeTest(col="data_size", min_val=_PAYLOAD_SIZE, max_val=_PAYLOAD_SIZE),
        TargetTest(col="exp_table_id", value=9, expected={"data_size": _PAYLOAD_SIZE}),
    ],
)


@pytest.fixture(scope="module")
def petexp_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_PETEXP_RESULT", None)
    if result is None:
        result = run_case(replace(PETEXP_CASE, tests=[]))
        request.module._PETEXP_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", PETEXP_CASE.tests, ids=case_id)
def test_petexp_dbss(spec: Any, petexp_result: HandlerResult) -> None:
    petexp_result.check(spec)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_petexpoffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    offset_result.check(spec)
