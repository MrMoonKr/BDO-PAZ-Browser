from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import (
    HandlerCase,
    HandlerResult,
    PaFieldTest,
    RangeTest,
    SchemaTest,
    TargetTest,
    case_id,
    header_count,
    run_case,
)


_REQUIRED_KEYS = [
    "group",
    "group_key",
    "group_name",
    "row",
    "unknown_00",
    "quest_chain_id",
    "quest_id",
    "packed_quest_id",
    "title",
    "condition",
    "unknown_05",
    "unknown_09",
    "unknown_0d",
]


def _list_case(name: str, tests: list) -> HandlerCase:
    file_name = f"{name}.bss"
    return HandlerCase(
        handler_name=file_name,
        data_file=file_name,
        companion_files={},
        loc_file="languagedata_en.loc",
        uses_loc=True,
        loc_fields=["Title", "Group Name", "Condition"],
        internal_path=f"gamecommondata/binary/{file_name}",
        tests=[
            SchemaTest(required_keys=_REQUIRED_KEYS),
            # Condition lines name NPCs and quests in yellow.
            PaFieldTest(field="condition"),
            *tests,
        ],
    )


NEWQUEST_CASE = _list_case("newquest", [
    # Zero in every row; a row read off its 17-byte stride would not be.
    RangeTest(col="unknown_00", min_val=0, max_val=0),
    TargetTest(
        col="packed_quest_id",
        value=600883,
        expected={
            "quest_chain_id": 11059,
            "quest_id": 9,
            "title": "[Event] Love for Pets",
            # The first group's key is the u32 at the start of its header.
            "group_key": 1,
        },
    ),
    TargetTest(
        col="packed_quest_id",
        value=77129,
        expected={"quest_chain_id": 11593, "quest_id": 1},
    ),
])

MAINQUEST_CASE = _list_case("mainquest", [
    # `1` on a few rows, `0` on the rest.
    RangeTest(col="unknown_00", min_val=0, max_val=1),
    TargetTest(
        col="packed_quest_id",
        value=105558,
        expected={
            "quest_chain_id": 40022,
            "quest_id": 1,
            "title": "[Special Growth] Birth of a Prestigious Family",
            "group_name": "[Special Growth] Taking My Own Path",
        },
    ),
])

RECOMMENDATIONQUEST_CASE = _list_case("recommendationquest", [
    RangeTest(col="unknown_00", min_val=0, max_val=0),
    TargetTest(
        col="packed_quest_id",
        value=171127,
        expected={
            "quest_chain_id": 40055,
            "quest_id": 2,
            "title": "[Life 101] Weasel Season",
            "group_name": "[Life 101] The Adventurer That Does It All",
        },
    ),
])

REPETITIONQUEST_CASE = _list_case("repetitionquest", [
    RangeTest(col="unknown_00", min_val=0, max_val=0),
    TargetTest(
        col="packed_quest_id",
        value=74644,
        expected={
            "quest_chain_id": 9108,
            "quest_id": 1,
            "title": "[Weekly] For the Throne: Aetherion",
        },
    ),
])

CASES = [NEWQUEST_CASE, MAINQUEST_CASE, RECOMMENDATIONQUEST_CASE, REPETITIONQUEST_CASE]
_RESULTS: dict[str, HandlerResult] = {}


def _result(case: HandlerCase) -> HandlerResult:
    result = _RESULTS.get(case.handler_name)
    if result is None:
        result = run_case(replace(case, tests=[]))
        _RESULTS[case.handler_name] = result
    return result


_SPECS = [(case, spec) for case in CASES for spec in case.tests]


@pytest.mark.parametrize(
    ("case", "spec"),
    _SPECS,
    ids=[f"{case.handler_name}-{case_id(spec)}" for case, spec in _SPECS],
)
def test_quest_list(case: HandlerCase, spec: Any) -> None:
    _result(case).check(spec)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.handler_name)
def test_quest_list_reaches_last_group(case: HandlerCase) -> None:
    # The file declares only a group count; each group header holds its own row count.
    result = _result(case)
    group_count = header_count(offset=4)(result.source)

    assert max(record["group"] for record in result.records) == group_count - 1


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.handler_name)
def test_every_group_has_a_name_and_every_row_a_condition(case: HandlerCase) -> None:
    """The list's LOC type names each group by its key and holds a condition line per quest."""
    for record in _result(case).records:
        assert record["group_name"], record["group"]
        assert record["condition"], record["packed_quest_id"]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.handler_name)
def test_group_keys_are_unique_per_group(case: HandlerCase) -> None:
    keys = {record["group"]: record["group_key"] for record in _result(case).records}

    assert len(set(keys.values())) == len(keys)
