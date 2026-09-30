from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from tests.framework import (
    HandlerCase,
    HandlerResult,
    SchemaTest,
    TargetTest,
    case_id,
    run_case,
)


_MENU_FILE = "menu.bss"
_STRINGTABLE_FILE = "stringtable.bss"

CASE = HandlerCase(
    handler_name="submenu.bss",
    data_file="submenu.bss",
    companion_files={_MENU_FILE: _MENU_FILE, _STRINGTABLE_FILE: _STRINGTABLE_FILE},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["title", "category"],
    internal_path="gamecommondata/binary/submenu.bss",
    tests=[
        SchemaTest(
            required_keys=[
                "entry_id",
                "menu_id",
                "position",
                "icon_path",
                "icon_region",
                "sheet",
                "title_key",
                "title",
                "category",
                "unknown_0c",
                "unknown_14",
            ],
        ),
        # A GAME sheet key and a RESOURCE sheet key, both in Information.
        TargetTest(
            col="title_key",
            value="LUA_MENU_REMAKE_MENU_HELP",
            expected={"title": "Adventurer's Guide (Help)", "category": "Information"},
        ),
        TargetTest(
            col="title_key",
            value="PANEL_MENU_NEWS_TITLE",
            expected={"title": "News", "sheet": "RESOURCE", "category": "Information"},
        ),
    ],
)


@pytest.fixture(scope="module")
def submenu_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_submenu_bss(spec: Any, submenu_result: HandlerResult) -> None:
    submenu_result.check(spec)


def test_every_entry_names_its_category(submenu_result: HandlerResult) -> None:
    # A bare menu ID would mean the category was not found in menu.bss.
    for record in submenu_result.records:
        assert record["category"] != str(record["menu_id"]), record["entry_id"]
