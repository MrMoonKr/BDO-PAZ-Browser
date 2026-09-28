from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from _dbss.dialogtext.text import plain_text, voice_name
from _dbss.dialogtext.parser import DialogTextLine
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

_OFFSET_FILE = "dialogtextoffset.dbss"
# The pool behind {GetRandomText(PEDU_47759_1)} in detail_dialog.dbss.
_PEDU_POOL = "PEDU_47759_1"

TEXT_CASE = HandlerCase(
    handler_name="dialogtext.dbss",
    data_file="dialogtext.dbss",
    companion_files={_OFFSET_FILE: _OFFSET_FILE},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Text"],
    internal_path="gamecommondata/binary/dialogtext.dbss",
    tests=[
        SchemaTest(required_keys=["key", "name", "line_count", "texts", "voices"]),
        DeclaredCountTest(declared=header_count(offset=0)),
        DeclaredCountTest(declared=header_count(offset=0, companion=_OFFSET_FILE)),
        TargetTest(col="name", value=_PEDU_POOL, expected={"key": 0x24E52C6C}),
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
        SchemaTest(required_keys=["key", "dbss_offset", "size"]),
        DeclaredCountTest(declared=header_count(offset=0)),
        TargetTest(col="key", value=0x24E52C6C, expected={}),
    ],
)


@pytest.fixture(scope="module")
def text_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_TEXT_RESULT", None)
    if result is None:
        result = run_case(replace(TEXT_CASE, tests=[]))
        request.module._TEXT_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", TEXT_CASE.tests, ids=case_id)
def test_dialogtext_dbss(spec: Any, text_result: HandlerResult) -> None:
    text_result.check(spec)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_dialogtextoffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    offset_result.check(spec)


def test_voiced_line_is_split_into_text_and_voice() -> None:
    # Line breaks are stored as the two characters "\n".
    line = DialogTextLine(1, "{AudioVoice(NPC_VCE_1_1_Test)}First line.\\nSecond line.")
    assert plain_text(line.text) == "First line. Second line."
    assert voice_name(line) == "NPC_VCE_1_1_Test"


def test_line_without_voice() -> None:
    line = DialogTextLine(1, "{ChangeScene(Scene_01)}Just text.")
    assert plain_text(line.text) == "Just text."
    assert voice_name(line) is None


def test_lines_use_the_user_language(text_result: HandlerResult) -> None:
    """Lines come from LOC type 36 when it is loaded."""
    pool = next(r for r in text_result.records if r["name"] == _PEDU_POOL)
    assert pool["texts"] and all(text.isascii() for text in pool["texts"])
