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

from _bss.questjournalvideoinfo.parser import build_quest_artwork_index


# [Storybook] Tale of the Mudang Wraith, the first journal video page.
_MUDANG_CHAIN = 8700
_MUDANG_QUEST = 11

CASE = HandlerCase(
    handler_name="questjournalvideoinfo.bss",
    data_file="questjournalvideoinfo.bss",
    companion_files={},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["title"],
    internal_path="gamecommondata/binary/questjournalvideoinfo.bss",
    tests=[
        SchemaTest(
            required_keys=[
                "quest_chain_id",
                "quest_id",
                "packed_quest_id",
                "video_path",
                "artwork_path",
                "title",
                "unknown_0c",
            ],
        ),
        DeclaredCountTest(declared=header_count(offset=4)),
        RangeTest(col="unknown_0c", min_val=0, max_val=1),
        TargetTest(
            col="packed_quest_id",
            value=_MUDANG_QUEST << 16 | _MUDANG_CHAIN,
            expected={
                "quest_chain_id": _MUDANG_CHAIN,
                "quest_id": _MUDANG_QUEST,
                "video_path": "ui_movie/pc/morningland/morningland_boss_03_02.bk2",
                "artwork_path": "ui_texture/icon/quest/morningland_boss_03_02_full.dds",
                "title": "[Storybook] Tale of the Mudang Wraith",
            },
        ),
    ],
)


@pytest.fixture(scope="module")
def questjournalvideoinfo_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_questjournalvideoinfo_bss(spec: Any, questjournalvideoinfo_result: HandlerResult) -> None:
    questjournalvideoinfo_result.check(spec)


def test_every_row_names_a_video_and_an_artwork(
    questjournalvideoinfo_result: HandlerResult,
) -> None:
    for record in questjournalvideoinfo_result.records:
        assert record["video_path"].endswith(".bk2"), record["packed_quest_id"]
        assert record["artwork_path"].endswith(".dds"), record["packed_quest_id"]


def test_each_quest_has_one_page(questjournalvideoinfo_result: HandlerResult) -> None:
    keys = [record["packed_quest_id"] for record in questjournalvideoinfo_result.records]
    assert len(keys) == len(set(keys))


def test_quest_artwork_index_matches_the_artwork_column(
    questjournalvideoinfo_result: HandlerResult,
) -> None:
    """IndexKind.QUEST_ARTWORK_ICON is this table's artwork by packed quest ID."""
    index = build_quest_artwork_index(questjournalvideoinfo_result.source.data)

    assert index == {
        r["packed_quest_id"]: r["artwork_path"] for r in questjournalvideoinfo_result.records
    }
