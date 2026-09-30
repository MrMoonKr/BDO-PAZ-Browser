from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import (
    DeclaredCountTest,
    HandlerCase,
    HandlerResult,
    SchemaTest,
    case_id,
    header_count,
    run_case,
)


_HOUSING_DIR = "ui_texture/icon/new_icon/03_etc/06_housing"
# Shimhyangje, a Land of the Morning Light manor with a wall and a floor blueprint.
_SHIMHYANGJE = 3842

CASE = HandlerCase(
    handler_name="mansionpartinfo.bss",
    data_file="mansionpartinfo.bss",
    companion_files={},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["manor"],
    internal_path="gamecommondata/binary/mansionpartinfo.bss",
    tests=[
        SchemaTest(
            required_keys=[
                "character_id",
                "manor",
                "part_index",
                "icon_path",
                "unknown_02",
                "unknown_str",
            ],
        ),
        DeclaredCountTest(declared=header_count(offset=4)),
    ],
)


@pytest.fixture(scope="module")
def mansionpartinfo_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_mansionpartinfo_bss(spec: Any, mansionpartinfo_result: HandlerResult) -> None:
    mansionpartinfo_result.check(spec)


def test_shimhyangje_has_its_wall_and_floor(mansionpartinfo_result: HandlerResult) -> None:
    parts = [r for r in mansionpartinfo_result.records if r["character_id"] == _SHIMHYANGJE]

    assert {r["manor"] for r in parts} == {"Shimhyangje"}
    assert {r["icon_path"] for r in parts} == {
        f"{_HOUSING_DIR}/mantion_morning1_wall.dds",
        f"{_HOUSING_DIR}/mantion_morning1_floor.dds",
    }


def test_parts_are_unique_per_manor(mansionpartinfo_result: HandlerResult) -> None:
    keys = [(r["character_id"], r["part_index"]) for r in mansionpartinfo_result.records]
    assert len(keys) == len(set(keys))
