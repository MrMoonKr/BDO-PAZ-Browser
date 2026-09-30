from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

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

from _bss.menu.titles import menu_title


_STRINGTABLE_FILE = "stringtable.bss"
# Information, the F1 category.
_INFORMATION_KEY = "LUA_MENU_REMAKE_CATEGORY_1"

CASE = HandlerCase(
    handler_name="menu.bss",
    data_file="menu.bss",
    companion_files={_STRINGTABLE_FILE: _STRINGTABLE_FILE},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["title"],
    internal_path="gamecommondata/binary/menu.bss",
    tests=[
        SchemaTest(
            required_keys=[
                "menu_id",
                "icon_path",
                "icon_region",
                "hotkey",
                "sheet",
                "title_key",
                "title",
                "submenu_count",
            ],
        ),
        DeclaredCountTest(declared=header_count(offset=4)),
        TargetTest(
            col="title_key",
            value=_INFORMATION_KEY,
            expected={"title": "Information", "hotkey": "F1", "sheet": "GAME"},
        ),
    ],
)


@pytest.fixture(scope="module")
def menu_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_menu_bss(spec: Any, menu_result: HandlerResult) -> None:
    menu_result.check(spec)


def test_titles_fall_back_to_the_key() -> None:
    record = {"sheet": "GAME", "title_key": "LUA_NOT_A_KEY"}

    assert menu_title(record, {}) == "LUA_NOT_A_KEY"
    assert menu_title({**record, "sheet": "NO_SUCH_SHEET"}, {"GAME": {"LUA_NOT_A_KEY": 1}}) == "LUA_NOT_A_KEY"
