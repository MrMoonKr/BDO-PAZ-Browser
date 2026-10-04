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


_CAT = 9101
_CAT_ICON = "New_UI_Common_forLua\\Window\\Stable\\Pet\\Pet_Cat_0991.dds"
# A pet record is a 32-byte header, the icon path and a 94-byte footer.
_PET_FIXED_SIZE = 32 + 94
# petexp.dbss stores at most 50 levels per EXP table.
_MAX_PET_LEVEL = 50

PET_CASE = HandlerCase(
    handler_name="pet.dbss",
    data_file="pet.dbss",
    companion_files={"petoffset.dbss": "petoffset.dbss", "petgrade.dbss": "petgrade.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["pet_name", "display_name"],
    internal_path="gamecommondata/binary/pet.dbss",
    tests=[
        SchemaTest(
            required_keys=[
                "pet_id",
                "variant",
                "species",
                "tier",
                "grade",
                "grade_name",
                "max_level",
                "equip_skill_slots",
                "acquire_type_id",
                "equip_skill_id",
                "icon_path",
                "unknown_12",
                "unknown_14",
                "unknown_53",
                "pet_id_match",
            ]
        ),
        DeclaredCountTest(declared=header_count()),
        # The key prefix, the header and the offset row all carry the same pet ID.
        RangeTest(col="pet_id_match", min_val=True, max_val=True),
        RangeTest(col="max_level", min_val=1, max_val=_MAX_PET_LEVEL),
        TargetTest(
            col="pet_id",
            value=_CAT,
            expected={
                "pet_name": "Cat",
                "display_name": "Cat",
                "variant": 2,
                "species": 1,
                "tier": 1,
                "grade": 1,
                "grade_name": "Classic",
                "icon_path": _CAT_ICON,
            },
        ),
        TargetTest(
            col="pet_id",
            value=64517,
            expected={
                "pet_name": "Golden Star",
                "display_name": "Golden Star",
                "variant": 1,
                "species": 105,
                "tier": 4,
                "grade": 2,
                "grade_name": "Rare",
                "icon_path": "New_UI_Common_forLua\\Window\\Stable\\Pet\\GoldStar_Pet_0004.dds",
            },
        ),
    ],
)

OFFSET_CASE = HandlerCase(
    handler_name="petoffset.dbss",
    data_file="petoffset.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/petoffset.dbss",
    tests=[
        SchemaTest(required_keys=["pet_id", "data_offset", "data_size"]),
        DeclaredCountTest(declared=header_count()),
        # The u16 size and the zero u16 after it read as one u32.
        RangeTest(col="data_size", min_val=0, max_val=0xFFFF),
        TargetTest(col="pet_id", value=_CAT, expected={"data_size": _PET_FIXED_SIZE + len(_CAT_ICON)}),
    ],
)

GRADE_CASE = HandlerCase(
    handler_name="petgrade.dbss",
    data_file="petgrade.dbss",
    companion_files={"petgradeoffset.dbss": "petgradeoffset.dbss"},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/petgrade.dbss",
    tests=[
        SchemaTest(
            required_keys=[
                "key",
                "variant",
                "species",
                "grade",
                "grade_name",
                "data_offset",
                "data_size",
                "key_match",
            ]
        ),
        DeclaredCountTest(declared=header_count()),
        # The key, its duplicate and the offset row key agree on every record.
        RangeTest(col="key_match", min_val=True, max_val=True),
        # Every record is 12 bytes: a 4-byte key prefix and 8 bytes of data.
        RangeTest(col="data_size", min_val=8, max_val=8),
        # 1-5 are labelled; 6 is open.
        RangeTest(col="grade", min_val=1, max_val=6),
        TargetTest(
            col="key",
            value=262,
            expected={"variant": 6, "species": 1, "grade": 3, "grade_name": "Premium"},
        ),
        TargetTest(
            col="key",
            value=15878,
            expected={"variant": 6, "species": 62, "grade": 2, "grade_name": "Rare"},
        ),
    ],
)

GRADE_OFFSET_CASE = HandlerCase(
    handler_name="petgradeoffset.dbss",
    data_file="petgradeoffset.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/petgradeoffset.dbss",
    tests=[
        SchemaTest(required_keys=["key", "variant", "species", "data_offset", "data_size"]),
        DeclaredCountTest(declared=header_count()),
        RangeTest(col="data_size", min_val=8, max_val=8),
        # The u16 key and the zero u16 after it read as one u32.
        RangeTest(col="key", min_val=0, max_val=0xFFFF),
        TargetTest(col="key", value=262, expected={"variant": 6, "species": 1}),
        TargetTest(col="key", value=9744, expected={"variant": 16, "species": 38}),
    ],
)


@pytest.fixture(scope="module")
def pet_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_PET_RESULT", None)
    if result is None:
        result = run_case(replace(PET_CASE, tests=[]))
        request.module._PET_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.fixture(scope="module")
def grade_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_GRADE_RESULT", None)
    if result is None:
        result = run_case(replace(GRADE_CASE, tests=[]))
        request.module._GRADE_RESULT = result
    return result


@pytest.fixture(scope="module")
def grade_offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_GRADE_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(GRADE_OFFSET_CASE, tests=[]))
        request.module._GRADE_OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", PET_CASE.tests, ids=case_id)
def test_pet_dbss(spec: Any, pet_result: HandlerResult) -> None:
    pet_result.check(spec)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_petoffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    offset_result.check(spec)


@pytest.mark.parametrize("spec", GRADE_CASE.tests, ids=case_id)
def test_petgrade_dbss(spec: Any, grade_result: HandlerResult) -> None:
    grade_result.check(spec)


@pytest.mark.parametrize("spec", GRADE_OFFSET_CASE.tests, ids=case_id)
def test_petgradeoffset_dbss(spec: Any, grade_offset_result: HandlerResult) -> None:
    grade_offset_result.check(spec)
