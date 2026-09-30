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

from _bss.groupcameradata.parser import build_cutscene_icon_index


_SYMBOL_DIR = "ui_texture/combine/icon/symbolicon"
# Send Off, the Balenos scene after the Cron Period Journal.
_SEND_OFF = 65

CASE = HandlerCase(
    handler_name="groupcameradata.bss",
    data_file="groupcameradata.bss",
    companion_files={},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["title", "description", "quote"],
    internal_path="gamecommondata/binary/groupcameradata.bss",
    tests=[
        SchemaTest(
            required_keys=[
                "scene_id",
                "icon_path",
                "title_kr",
                "description_kr",
                "quote_kr",
                "title",
                "description",
                "quote",
            ],
        ),
        DeclaredCountTest(declared=header_count(offset=4)),
        TargetTest(
            col="scene_id",
            value=_SEND_OFF,
            expected={
                "icon_path": f"{_SYMBOL_DIR}/symbolicon_valenos.dds",
                "title_kr": "환송",
                "title": "Send Off",
            },
        ),
    ],
)


@pytest.fixture(scope="module")
def groupcameradata_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_groupcameradata_bss(spec: Any, groupcameradata_result: HandlerResult) -> None:
    groupcameradata_result.check(spec)


def test_scene_ids_are_unique(groupcameradata_result: HandlerResult) -> None:
    ids = [r["scene_id"] for r in groupcameradata_result.records]
    assert len(ids) == len(set(ids))


def test_every_scene_has_korean_text_and_an_icon(groupcameradata_result: HandlerResult) -> None:
    for record in groupcameradata_result.records:
        assert record["title_kr"] and record["description_kr"], record["scene_id"]
        assert record["icon_path"].startswith(f"{_SYMBOL_DIR}/"), record["scene_id"]


def test_cutscene_icon_index_matches_the_icon_column(groupcameradata_result: HandlerResult) -> None:
    """IndexKind.CUTSCENE_ICON is this table's icons by scene ID."""
    index = build_cutscene_icon_index(groupcameradata_result.source.data)

    assert index == {r["scene_id"]: r["icon_path"] for r in groupcameradata_result.records}
