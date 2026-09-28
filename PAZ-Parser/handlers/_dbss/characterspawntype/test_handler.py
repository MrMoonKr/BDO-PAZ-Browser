from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import (
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

from _dbss.characterspawntype.parser import SPAWN_TYPE_NAMES


_RECORD_SIZE = 48


def _spawn_type_record(record: dict) -> dict:
    return {
        **record,
        "active_roles": [SPAWN_TYPE_NAMES[i] for i, value in enumerate(record["roles"]) if value],
    }


SPAWN_TYPE_CASE = HandlerCase(
    handler_name="characterspawntype.dbss",
    data_file="characterspawntype.dbss",
    companion_files={"characterspawntypeoffset.dbss": "characterspawntypeoffset.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Name"],
    internal_path="gamecommondata/binary/characterspawntype.dbss",
    record_mapper=_spawn_type_record,
    tests=[
        SchemaTest(required_keys=["character_id", "name_en", "roles", "active_roles"]),
        DeclaredCountTest(declared=header_count()),
        TargetTest(col="character_id", value=47727, expected={"name_en": "Jackson"}),
        # Read as a u32, this row looked like entity 82176: the NormalNpc byte
        # sat in the high half of the ID.
        TargetTest(col="character_id", value=16640, expected={"active_roles": ["NormalNpc"]}),
        TargetTest(
            col="character_id",
            value=47659,
            expected={
                "active_roles": ["ItemRepairer", "ImportantNpc", "Stable", "Intimacy", "Mating", "Grocery"],
            },
        ),
    ],
)

OFFSET_CASE = HandlerCase(
    handler_name="characterspawntypeoffset.dbss",
    data_file="characterspawntypeoffset.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/characterspawntypeoffset.dbss",
    tests=[
        SchemaTest(required_keys=["character_id", "offset", "size"]),
        DeclaredCountTest(declared=header_count(offset=4)),
        RangeTest(col="size", min_val=_RECORD_SIZE, max_val=_RECORD_SIZE),
        # The first record follows the main file's 4-byte count.
        TargetTest(col="offset", value=4, expected={"size": _RECORD_SIZE}),
    ],
)


@pytest.fixture(scope="module")
def spawn_type_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_SPAWN_TYPE_RESULT", None)
    if result is None:
        result = run_case(replace(SPAWN_TYPE_CASE, tests=[]))
        request.module._SPAWN_TYPE_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", SPAWN_TYPE_CASE.tests, ids=case_id)
def test_characterspawntype_dbss(spec: Any, spawn_type_result: HandlerResult) -> None:
    spawn_type_result.check(spec)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_characterspawntypeoffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    offset_result.check(spec)


def test_characterspawntype_role_flags_are_0_or_1(spawn_type_result: HandlerResult) -> None:
    bad = [
        record["character_id"]
        for record in spawn_type_result.records
        if any(value not in (0, 1) for value in record["roles"])
    ]
    assert not bad, f"role bytes other than 0 or 1 on characters {bad[:5]}"
