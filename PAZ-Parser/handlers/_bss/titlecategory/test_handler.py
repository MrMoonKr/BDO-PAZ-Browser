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
    run_case,
)


_HEADER_SIZE = 8
_TRAILER_SIZE = 12


def _listed_titles() -> DeclaredCount:
    """Title IDs in the category lists: the PABR trailer's end-of-entries
    offset, less the 8-byte header and one u32 count per category."""

    def read(source: CaseInput) -> int:
        raw = source.file(None)
        category_count = int.from_bytes(raw[4:8], "little")
        end_of_entries = int.from_bytes(raw[-_TRAILER_SIZE + 4:-_TRAILER_SIZE + 8], "little")
        if raw[:4] != b"PABR" or end_of_entries != len(raw) - _TRAILER_SIZE:
            raise AssertionError(f"{len(raw)} bytes do not end in a PABR trailer")
        return (end_of_entries - _HEADER_SIZE) // 4 - category_count

    return read


CASE = HandlerCase(
    handler_name="titlecategory.bss",
    data_file="titlecategory.bss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/customization/titlecategory.bss",
    tests=[
        SchemaTest(required_keys=["title_id", "category_id"]),
        DeclaredCountTest(declared=_listed_titles()),
        # title.dbss categories: World, Combat, Life Skill, Fishing.
        RangeTest(col="category_id", min_val=0, max_val=3),
        TargetTest(col="title_id", value=1, expected=[{"category_id": 1, "category": "Combat"}]),
        TargetTest(col="title_id", value=218, expected=[{"category_id": 3, "category": "Fishing"}]),
    ],
)


@pytest.fixture(scope="module")
def titlecategory_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_titlecategory_bss(spec: Any, titlecategory_result: HandlerResult) -> None:
    titlecategory_result.check(spec)
