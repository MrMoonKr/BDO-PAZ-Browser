from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import CountTest, HandlerCase, HandlerResult, PosTest, SchemaTest, TargetTest, case_id, run_case


STATIC_CASE = HandlerCase(
    handler_name="characterstatic.dbss",
    data_file="characterstatic.dbss",
    companion_files={"characterstaticoffset.dbss": "characterstaticoffset.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Name"],
    internal_path="gamecommondata/binary/characterstatic.dbss",
    tests=[
        SchemaTest(
            required_keys=[
                "character_id", "name_en", "action_script", "condition_script",
                "knowledge_id", "npc_kind", "class_type", "model_path", "payload_size",
            ]
        ),
        CountTest(expected=24017),
        PosTest(
            pos=0,
            expected={
                "character_id": 47759,
                "name_en": "Edania Merchant",
                "action_script": "getknowledge(14469);",
                "condition_script": "",
                "knowledge_id": 14469,
                "payload_size": 586,
                "npc_kind": 2,
                "class_type": None,
                "model_path": "npc/pedu/npc_pedu_named",
            },
        ),
        TargetTest(
            col="character_id",
            value=16640,
            expected={
                "name_en": "Dev Plant210",
                "action_script": "",
                "knowledge_id": None,
                "payload_size": 511,
                "npc_kind": 8,
                "model_path": "monster/dummy_normal",
            },
        ),
        # A condition script used to be misread into the action script and
        # shifted every field after it.
        TargetTest(
            col="character_id",
            value=47332,
            expected={
                "action_script": "getknowledge(2095);",
                "condition_script": "getOceanTendency()>-1;",
                "knowledge_id": 2095,
                "npc_kind": 2,
            },
        ),
        # The getknowledge match ignores case.
        TargetTest(col="character_id", value=50613, expected={"knowledge_id": 933}),
        # class_type differs from character_id: Warrior is 1 / 0, Ranger 2 / 4.
        TargetTest(
            col="character_id",
            value=1,
            expected={"class_type": 0, "model_path": "pc/1_phm/fighteraction_noweapon"},
        ),
        TargetTest(col="character_id", value=2, expected={"class_type": 4}),
    ],
)

OFFSET_CASE = HandlerCase(
    handler_name="characterstaticoffset.dbss",
    data_file="characterstaticoffset.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/characterstaticoffset.dbss",
    tests=[
        SchemaTest(required_keys=["character_id", "offset", "size"]),
        CountTest(expected=24017),
        PosTest(pos=0, expected={"character_id": 47759, "offset": 6, "size": 586}),
        PosTest(pos=-1, expected={"character_id": 16640, "offset": 13563768, "size": 511}),
    ],
)


@pytest.fixture(scope="module")
def static_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_STATIC_RESULT", None)
    if result is None:
        result = run_case(replace(STATIC_CASE, tests=[]))
        request.module._STATIC_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", STATIC_CASE.tests, ids=case_id)
def test_characterstatic_dbss(spec: Any, static_result: HandlerResult) -> None:
    static_result.check(spec)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_characterstaticoffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    offset_result.check(spec)
