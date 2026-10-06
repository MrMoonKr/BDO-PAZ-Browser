from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from _dbss.knowledgelearning.parser import SOURCE_CHARACTER, parse_knowledgelearning_records
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


_LEARNING_FILE = "knowledgelearning.dbss"
_LEARNING_OFFSET_FILE = "knowledgelearningoffset.dbss"

CASE = HandlerCase(
    handler_name="knowledgelearningcharacterkey.bss",
    data_file="knowledgelearningcharacterkey.bss",
    # Not read by the handler; the cross-check below compares every entry with them.
    companion_files={_LEARNING_FILE: _LEARNING_FILE, _LEARNING_OFFSET_FILE: _LEARNING_OFFSET_FILE},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["card_name"],
    internal_path="gamecommondata/binary/knowledgelearningcharacterkey.bss",
    tests=[
        SchemaTest(required_keys=["card_id", "card_name", "character_count", "character_ids", "characters"]),
        DeclaredCountTest(declared=header_count(offset=0)),
        # Two copies of one monster teach its card, kept in the stored order.
        TargetTest(
            col="card_id",
            value=4174,
            expected={
                "card_name": "Demibeast Bandit Warrior",
                "character_ids": [24444, 20170],
                "characters": ["24444 Demibeast Bandit Warrior", "20170 Demibeast Bandit Warrior"],
            },
        ),
        TargetTest(
            col="card_id",
            value=4686,
            expected={"card_name": "Khuruto Chaser", "character_ids": [20665], "characters": ["20665 Khuruto Chaser"]},
        ),
    ],
)


@pytest.fixture(scope="module")
def knowledgelearningcharacterkey_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_knowledgelearningcharacterkey_bss(spec: Any, knowledgelearningcharacterkey_result: HandlerResult) -> None:
    knowledgelearningcharacterkey_result.check(spec)


def test_entries_group_the_knowledgelearning_character_table(
    knowledgelearningcharacterkey_result: HandlerResult,
) -> None:
    """Every character row of knowledgelearning.dbss, grouped by card in row order."""
    source = knowledgelearningcharacterkey_result.source
    expected: dict[int, list[int]] = {}
    for record in parse_knowledgelearning_records(source.file(_LEARNING_FILE), source.file(_LEARNING_OFFSET_FILE)):
        if record.source_type == SOURCE_CHARACTER:
            expected.setdefault(record.card_id, []).append(record.source_id)

    actual = {r["card_id"]: r["character_ids"] for r in knowledgelearningcharacterkey_result.records}
    assert actual == expected
