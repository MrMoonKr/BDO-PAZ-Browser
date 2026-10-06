from __future__ import annotations

import struct
from dataclasses import replace
from typing import Any

import pytest

from tests.case_input import CaseInput
from tests.framework import (
    DeclaredCountTest,
    HandlerCase,
    HandlerResult,
    RangeTest,
    SchemaTest,
    TargetTest,
    case_id,
    run_case,
)

from _bss.employeestaticstatus.display import stat_text, weight_text
from _bss.employeestaticstatus.parser import STAT_FIELDS, parse_employeestaticstatus_records


_ROW_SIZE = 130
_ICON_FOLDER = "Icon/New_Icon/11_Employee/"


def _both_list_counts(source: CaseInput) -> int:
    """The sailor count after the magic plus the First Mate count after the sailor rows."""
    sailors = struct.unpack_from("<I", source.data, 4)[0]
    first_mates = struct.unpack_from("<I", source.data, 8 + sailors * _ROW_SIZE)[0]
    return sailors + first_mates


CASE = HandlerCase(
    handler_name="employeestaticstatus.bss",
    data_file="employeestaticstatus.bss",
    companion_files={"stringtable.bss": "stringtable.bss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Name", "Title"],
    internal_path="gamecommondata/binary/employeestaticstatus.bss",
    tests=[
        SchemaTest(
            required_keys=[
                "employee_key",
                "level",
                "job",
                "job_label",
                "character_id",
                "name",
                "title",
                "icon_index",
                "icon_path",
                "abilities",
                "other_abilities",
                "first_mate_skill",
                *STAT_FIELDS.values(),
                "weight",
                "cabin_cost",
                "appetite",
                "max_condition",
                "unknown_74",
            ],
        ),
        DeclaredCountTest(declared=_both_list_counts),
        RangeTest(col="job", min_val=0, max_val=1),
        TargetTest(
            col="employee_key",
            value=23,
            expected={
                "character_id": 59228,
                "name": "Pacuna",
                "job_label": "Sailor",
                "icon_path": f"{_ICON_FOLDER}Employee_59228.dds",
            },
        ),
        TargetTest(col="employee_key", value=1, expected={"character_id": 59053, "title": "<Ambitious>"}),
        # The First Mates sit in the second list; the sailor Lua names their skills by these keys.
        TargetTest(col="character_id", value=62167, expected={"employee_key": 24, "job": 1, "name": "Cleia"}),
        TargetTest(col="character_id", value=62169, expected={"employee_key": 26, "job_label": "First Mate"}),
    ],
)


@pytest.fixture(scope="module")
def employeestaticstatus_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_employeestaticstatus_bss(spec: Any, employeestaticstatus_result: HandlerResult) -> None:
    employeestaticstatus_result.check(spec)


def test_every_icon_is_the_rows_character(employeestaticstatus_result: HandlerResult) -> None:
    # Checks the icon index: each sailor's portrait is named after its character.
    for record in employeestaticstatus_result.records:
        assert record["icon_path"].endswith(f"Employee_{record['character_id']}.dds"), record


_SHIP_STATS = ("endurance", "wits", "awareness", "strength")


def test_sailors_have_ship_stats_and_first_mates_none(employeestaticstatus_result: HandlerResult) -> None:
    # Checks the stat names: every sailor has all four ship stats, a First Mate none.
    for record in employeestaticstatus_result.records:
        has_stats = [record[field] > 0 for field in _SHIP_STATS]
        assert all(has_stats) if record["job"] == 0 else not any(has_stats), record


_SKILLED_FIRST_MATES = {62167, 62168, 62169}


def test_only_named_first_mates_have_a_skill(employeestaticstatus_result: HandlerResult) -> None:
    # Checks the skill lookup: the three keys the sailor Lua names get text, every other row none.
    for record in employeestaticstatus_result.records:
        assert bool(record["first_mate_skill"]) == (record["character_id"] in _SKILLED_FIRST_MATES), record


def test_stat_and_weight_text() -> None:
    assert stat_text(16000) == "1.6%"
    assert stat_text(0) == "0.0%"
    assert weight_text(2_500_000) == "250 LT"
    assert weight_text(125_000) == "12.5 LT"


def test_bad_magic_raises() -> None:
    with pytest.raises(ValueError, match="invalid magic"):
        parse_employeestaticstatus_records(b"XXXX" + bytes(16))
