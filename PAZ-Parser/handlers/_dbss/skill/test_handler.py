from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from _common.lookup_index import IndexKind
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

_OFFSET_FILE = "skilloffset.dbss"
_SKILLTYPE_OFFSET_FILE = "skilltypeoffset.dbss"
# Item 761880 casts skill 47683 level 1, which applies buffs 48723 to 48728.
_ITEM_SKILL_KEY = 47683 << 16 | 1
# Grave Digging I leads to Grave Digging II (skill 1760).
_GRAVE_DIGGING_I = 1759 << 16 | 1
_GRAVE_DIGGING_II = 1760 << 16 | 1
# Looks like a sentinel, but is the ordinary skill 57005.
_DEAD_KEY = 0xDEAD0001
_GRAVE_DIGGING_ICON = "ui_texture/icon/New_Icon/04_PC_Skill/01_PC_Skill/01_PHM_Skill/PHM_Skill_1759.dds"

SKILL_CASE = HandlerCase(
    handler_name="skill.dbss",
    data_file="skill.dbss",
    companion_files={_OFFSET_FILE: _OFFSET_FILE},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Name", "Description", "Buffs", "Next Skills", "Base Skill"],
    internal_path="gamecommondata/binary/skill.dbss",
    lookup_indexes={IndexKind.SKILL_ICON: {1759: _GRAVE_DIGGING_ICON}},
    tests=[
        SchemaTest(required_keys=[
            "skill_key", "skill_no", "level", "icon_path", "name", "description", "cooldown_ms", "resource_cost",
            "stamina_cost", "buff_ids", "buffs",
            "next_skill_keys", "base_skill_keys", "script",
        ]),
        DeclaredCountTest(declared=header_count(offset=0)),
        DeclaredCountTest(declared=header_count(offset=4, companion=_OFFSET_FILE)),
        RangeTest(col="level", min_val=1, max_val=0xFFFF),
        TargetTest(
            col="skill_key",
            value=_ITEM_SKILL_KEY,
            expected={"skill_no": 47683, "level": 1, "buff_ids": [48723, 48724, 48725, 48726, 48727, 48728]},
        ),
        TargetTest(
            col="skill_key",
            value=_GRAVE_DIGGING_I,
            expected={"skill_no": 1759, "name": "Grave Digging I", "icon_path": _GRAVE_DIGGING_ICON},
        ),
        TargetTest(col="skill_key", value=_DEAD_KEY, expected={"skill_no": 57005, "level": 1}),
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
        SchemaTest(required_keys=["skill_key", "skill_no", "level", "dbss_offset", "size"]),
        DeclaredCountTest(declared=header_count(offset=4)),
        TargetTest(col="skill_key", value=_ITEM_SKILL_KEY, expected={"skill_no": 47683, "level": 1}),
    ],
)

# skilltypeoffset.dbss shares the handler; every key is level 1.
SKILLTYPE_OFFSET_CASE = replace(
    OFFSET_CASE,
    handler_name=_SKILLTYPE_OFFSET_FILE,
    data_file=_SKILLTYPE_OFFSET_FILE,
    internal_path=f"gamecommondata/binary/{_SKILLTYPE_OFFSET_FILE}",
    tests=[
        DeclaredCountTest(declared=header_count(offset=4)),
        RangeTest(col="level", min_val=1, max_val=1),
    ],
)


@pytest.fixture(scope="module")
def skill_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_SKILL_RESULT", None)
    if result is None:
        result = run_case(replace(SKILL_CASE, tests=[]))
        request.module._SKILL_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.fixture(scope="module")
def skilltype_offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_SKILLTYPE_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(SKILLTYPE_OFFSET_CASE, tests=[]))
        request.module._SKILLTYPE_OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", SKILL_CASE.tests, ids=case_id)
def test_skill_dbss(spec: Any, skill_result: HandlerResult) -> None:
    skill_result.check(spec)


def test_skill_rank_leads_to_next_rank(skill_result: HandlerResult) -> None:
    grave_digging = next(r for r in skill_result.records if r["skill_key"] == _GRAVE_DIGGING_I)
    assert _GRAVE_DIGGING_II in grave_digging["next_skill_keys"]


def test_every_linked_skill_is_a_skill_key(skill_result: HandlerResult) -> None:
    keys = {r["skill_key"] for r in skill_result.records}
    linked = {key for r in skill_result.records for key in r["next_skill_keys"] + r["base_skill_keys"]}
    assert linked <= keys


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_skilloffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    offset_result.check(spec)


@pytest.mark.parametrize("spec", SKILLTYPE_OFFSET_CASE.tests, ids=case_id)
def test_skilltypeoffset_dbss(spec: Any, skilltype_offset_result: HandlerResult) -> None:
    skilltype_offset_result.check(spec)


def test_records_open_in_skill_key_order(skill_result: HandlerResult) -> None:
    keys = [r["skill_key"] for r in skill_result.records]
    assert keys == sorted(keys)


def test_descriptions_are_display_text(skill_result: HandlerResult) -> None:
    for r in skill_result.records:
        assert "<PA" not in r["description"], r["skill_key"]
        assert r["description"] not in {"<null>", "UNKNOWN"}, r["skill_key"]

