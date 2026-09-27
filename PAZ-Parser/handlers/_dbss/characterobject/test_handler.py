from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import CountTest, HandlerCase, HandlerResult, PosTest, RangeTest, SchemaTest, TargetTest, case_id, run_case


OBJECT_CASE = HandlerCase(
    handler_name="characterobject.dbss",
    data_file="characterobject.dbss",
    companion_files={"characterobjectoffset.dbss": "characterobjectoffset.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Name"],
    internal_path="gamecommondata/binary/characterobject.dbss",
    tests=[
        SchemaTest(required_keys=["character_id", "icon_path", "name_en", "object_kind", "model_path"]),
        CountTest(expected=5123),
        RangeTest(col="object_kind", min_val=0, max_val=37),
        PosTest(
            pos=0,
            expected={
                "character_id": 16111,
                "name_en": "Golden Hand Vase",
                "object_kind": 2,
                "model_path": "00_Common/Pot/Pot_Base_48.pam",
            },
        ),
        PosTest(
            pos=-1,
            expected={"character_id": 16640, "object_kind": 2, "model_path": "Weed_Sunflower_01.srt"},
        ),
        TargetTest(
            col="character_id",
            value=1001,
            expected={
                "name_en": "Metal Processing Tool",
                "object_kind": 2,
                "model_path": "00_Common/Crafting/Crafting_Smithing_01.pam",
            },
        ),
        TargetTest(
            col="character_id",
            value=2101,
            expected={"object_kind": 5, "model_path": "02_balenos/velia/balenos_velia_str_house_05.pam"},
        ),
    ],
)

OFFSET_CASE = HandlerCase(
    handler_name="characterobjectoffset.dbss",
    data_file="characterobjectoffset.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/characterobjectoffset.dbss",
    tests=[
        SchemaTest(required_keys=["character_id", "offset", "size"]),
        CountTest(expected=5123),
        PosTest(pos=0, expected={"character_id": 16111, "offset": 3011279, "size": 714}),
        PosTest(pos=-1, expected={"character_id": 16640, "offset": 703168, "size": 712}),
    ],
)


@pytest.fixture(scope="module")
def object_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OBJECT_RESULT", None)
    if result is None:
        result = run_case(replace(OBJECT_CASE, tests=[]))
        request.module._OBJECT_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", OBJECT_CASE.tests, ids=case_id)
def test_characterobject(spec: Any, object_result: HandlerResult) -> None:
    spec.check(object_result.records)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_characterobjectoffset(spec: Any, offset_result: HandlerResult) -> None:
    spec.check(offset_result.records)
