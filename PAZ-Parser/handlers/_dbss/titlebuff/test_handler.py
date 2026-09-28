from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import (
    DeclaredCountTest,
    HandlerCase,
    HandlerResult,
    SchemaTest,
    TargetTest,
    case_id,
    header_count,
    run_case,
)


BUFF_CASE = HandlerCase(
    handler_name="titlebufflist.dbss",
    data_file="titlebufflist.dbss",
    companion_files={"titlebufflistoffset.dbss": "titlebufflistoffset.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Text"],
    internal_path="gamecommondata/binary/titlebufflist.dbss",
    tests=[
        SchemaTest(required_keys=["level", "required_titles", "text", "offset"]),
        DeclaredCountTest(declared=header_count(companion="titlebufflistoffset.dbss")),
        # The first tier follows the u32 count.
        TargetTest(col="level", value=1, expected={"offset": 4}),
    ],
)

OFFSET_CASE = HandlerCase(
    handler_name="titlebufflistoffset.dbss",
    data_file="titlebufflistoffset.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/titlebufflistoffset.dbss",
    tests=[
        SchemaTest(required_keys=["buff_id", "offset"]),
        DeclaredCountTest(declared=header_count()),
        TargetTest(col="buff_id", value=0, expected={"offset": 4}),
    ],
)


@pytest.fixture(scope="module")
def buff_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_BUFF_RESULT", None)
    if result is None:
        result = run_case(replace(BUFF_CASE, tests=[]))
        request.module._BUFF_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", BUFF_CASE.tests, ids=case_id)
def test_titlebufflist_dbss(spec: Any, buff_result: HandlerResult) -> None:
    buff_result.check(spec)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_titlebufflistoffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    offset_result.check(spec)


def test_titlebufflist_text_matches_required_titles(buff_result: HandlerResult) -> None:
    """Each tier's LOC line is the one for its own title count."""
    for record in buff_result.records:
        prefix = f"Acquire x{record['required_titles']:,}:"
        assert record["text"].startswith(prefix), f"level {record['level']}: {record['text']!r}"
