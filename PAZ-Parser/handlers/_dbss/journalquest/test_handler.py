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
    PaFieldTest,
    RangeTest,
    SchemaTest,
    TargetTest,
    case_id,
    run_case,
)


def _offset_rows(companion: str | None = None) -> DeclaredCount:
    """Book rows in journalquestoffset.dbss: its u32 words minus the group
    count and each group's (key, count) pair, three words per book."""

    def read(source: CaseInput) -> int:
        raw = source.file(companion)
        group_count = int.from_bytes(raw[:4], "little")
        book_words = len(raw) // 4 - 1 - 2 * group_count
        if len(raw) % 4 or book_words < 0 or book_words % 3:
            raise AssertionError(f"{len(raw)} bytes do not hold {group_count} groups of 12-byte books")
        return book_words // 3

    return read


OFFSET_CASE = HandlerCase(
    handler_name="journalquestoffset.dbss",
    data_file="journalquestoffset.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/journalquestoffset.dbss",
    tests=[
        SchemaTest(required_keys=["group_id", "entry_no", "byte_offset", "byte_size"]),
        DeclaredCountTest(declared=_offset_rows()),
        # The first book follows the data file's group count and first book count.
        TargetTest(col="group_id", value=1, expected={"entry_no": 1, "byte_offset": 8}),
        TargetTest(col="group_id", value=10, expected={"entry_no": 1}),
    ],
)


CASE = HandlerCase(
    handler_name="journalquest.dbss",
    data_file="journalquest.dbss",
    companion_files={"journalquestoffset.dbss": "journalquestoffset.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["page_titles_text"],
    internal_path="gamecommondata/binary/journalquest.dbss",
    tests=[
        SchemaTest(
            required_keys=[
                "group_id",
                "entry_no",
                "is_record_book",
                "journal_cat_id",
                "journal_title",
                "page_vol_title",
                "page_count",
                "combine_model",
                "static_model",
                "page_titles_text",
            ]
        ),
        DeclaredCountTest(declared=_offset_rows("journalquestoffset.dbss")),
        RangeTest(col="is_record_book", min_val=0, max_val=1),
        RangeTest(col="terminal", min_val=0, max_val=0),
        # Unlock conditions name their quests in colour.
        PaFieldTest(field="unlock_condition_text"),
        TargetTest(
            col="journal_cat_id",
            value=748,
            expected={
                "group_id": 1,
                "entry_no": 1,
                "journal_title": "이고르 바탈리의 모험일지",
                "journal_title_text": "Igor Bartali's Adventures",
                # Read through its u64 length; the old scan kept the next length's low byte.
                "combine_model": "Combine_Etc_Adventure_Bookshelf01",
                "static_model": "Adventure_Bookshelf_Static_book_00",
            },
        ),
        TargetTest(
            col="journal_cat_id",
            value=30006,
            expected={
                "group_id": 2,
                "entry_no": 1,
                "journal_title_text": "Shakatu Merchants' Archive",
            },
        ),
        # Storybook - Donghae is a record book: its pages fill in from knowledge.
        TargetTest(col="group_id", value=7, expected={"is_record_book": 1}),
    ],
)


@pytest.fixture(scope="module")
def journalquestoffset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_HANDLER_RESULT = result
    return result


@pytest.fixture(scope="module")
def journalquest_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_journalquestoffset_dbss(spec: Any, journalquestoffset_result: HandlerResult) -> None:
    journalquestoffset_result.check(spec)


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_journalquest_dbss(spec: Any, journalquest_result: HandlerResult) -> None:
    journalquest_result.check(spec)
