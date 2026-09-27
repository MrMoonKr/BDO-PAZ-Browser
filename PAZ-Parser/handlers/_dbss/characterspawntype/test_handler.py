from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import CountTest, HandlerCase, HandlerResult, PosTest, SchemaTest, TargetTest, case_id, run_case

from _dbss.characterspawntype.parser import SPAWN_TYPE_NAMES


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
        CountTest(expected=24017),
        PosTest(pos=0, expected={"character_id": 47759, "name_en": "Edania Merchant", "active_roles": ["ImportantNpc"]}),
        # Read as a u32, this row looked like entity 82176: the NormalNpc byte
        # sat in the high half of the ID.
        PosTest(pos=-1, expected={"character_id": 16640, "active_roles": ["NormalNpc"]}),
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
        CountTest(expected=24017),
        PosTest(pos=0, expected={"character_id": 47759, "offset": 4, "size": 48}),
        PosTest(pos=-1, expected={"character_id": 16640, "offset": 1152772, "size": 48}),
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
    spec.check(spawn_type_result.records)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_characterspawntypeoffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    spec.check(offset_result.records)
