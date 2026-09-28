from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from bdo_models import PazEntry
from bdo_preview import get_handler
from tests.fixtures import ensure_fixtures
from tests.framework import (
    CountTest,
    HandlerCase,
    HandlerResult,
    PosTest,
    RangeTest,
    SchemaTest,
    TargetTest,
    case_id,
    run_case,
)


def _quest_record(record: dict) -> dict:
    loc_texts = record.get("loc_texts_en", [])
    mapped = dict(record)
    mapped["title_en"] = loc_texts[0] if loc_texts else ""
    mapped["objective_en"] = loc_texts[3] if len(loc_texts) > 3 else ""
    return mapped


CASE = HandlerCase(
    handler_name="quest.dbss",
    data_file="quest.dbss",
    companion_files={"allquestlist.bss": "allquestlist.bss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Title", "Objective"],
    internal_path="gamecommondata/binary/quest.dbss",
    record_mapper=_quest_record,
    tests=[
        SchemaTest(
            required_keys=[
                "row",
                "offset",
                "size",
                "packed_quest_id",
                "quest_chain_id",
                "quest_id",
                "quest_category",
                "block_kind",
                "condition_script",
                "action_script",
                "objective_text_kr",
                "title_en",
                "icon_path",
                "family_stats",
                "family_stat_text",
            ]
        ),
        # Every record, walked in allquestlist.bss order.
        CountTest(expected=19_599),
        RangeTest(col="quest_category", min_val=0, max_val=19),
        PosTest(
            pos=0,
            expected={
                "row": 0,
                "offset": 0x4,
                "packed_quest_id": 1050655,
                "quest_chain_id": 2079,
                "quest_id": 16,
                "quest_category": 3,
                "condition_script": "checkFieldType(hadumField);getLevel()>59;clearquest(2080,10);",
                "action_script": "killMonsterGroup(189,1);",
                "objective_text_kr": "<악몽의 그림자> 기가고드 처치하기;",
                "title_en": "[Elvia Weekly] Gigagord",
                "objective_en": "Defeat <Shadow of Nightmares> Gigagord;",
                "icon_path": "Icon/Quest/Hadum08.dds",
                "family_stat_text": None,
            },
        ),
        PosTest(pos=1, expected={"offset": 0x5F8, "packed_quest_id": 463223}),
        PosTest(
            pos=2,
            expected={
                "offset": 0x936,
                "packed_quest_id": 6751209,
                "condition_script": "getLevel()>30;<or>clearquest(654,4);",
                "icon_path": "Icon/Quest/Imp.dds",
            },
        ),
        # The old icon-anchored scan read this record's scripts as icon-only.
        TargetTest(
            col="packed_quest_id",
            value=1510453,
            expected={
                "row": 101,
                "quest_chain_id": 3125,
                "quest_id": 23,
                "title_en": "Puzzling Words",
                "condition_script": "clearQuest(3125,22);",
                "action_script": "meet(50575,1);",
                "icon_path": "Icon/Quest/BalenosExplore_01.dds",
            },
        ),
        # An ordinary quest granting a Family stat from reward entry 1.
        TargetTest(
            col="packed_quest_id",
            value=72350,
            expected={
                "family_stats": [{"entry": 1, "type": 1, "label": "DP", "value": 1.0}],
                "family_stat_text": "DP +1",
            },
        ),
        # A journal page (category 11) with its Family stat in entry 0.
        TargetTest(
            col="packed_quest_id",
            value=197406,
            expected={"quest_category": 11, "family_stat_text": "Stamina +35"},
        ),
        # One of the three records that store no icon path.
        TargetTest(col="packed_quest_id", value=69183, expected={"icon_path": ""}),
    ],
)


@pytest.fixture(scope="module")
def quest_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.fixture(scope="module")
def quest_lazy_context() -> tuple[Any, bytes, PazEntry, dict[str, bytes]]:
    fixture_paths = ensure_fixtures(CASE)

    from _common.loc import init_loc

    init_loc(fixture_paths[str(CASE.loc_file)].read_bytes())
    entry = PazEntry(
        archive_name="",
        internal_path=CASE.internal_path,
        offset=0,
        compressed_size=0,
        uncompressed_size=0,
        compression_type=0,
        encryption_type=0,
    )
    handler = get_handler("quest.dbss", ".dbss")
    companions = {
        name: fixture_paths[name].read_bytes() for name in CASE.companion_files
    }
    return handler, fixture_paths[str(CASE.data_file)].read_bytes(), entry, companions


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_quest_dbss(spec: Any, quest_result: HandlerResult) -> None:
    quest_result.check(spec)


def test_quest_dbss_lazy_page(quest_lazy_context: tuple[Any, bytes, PazEntry, dict[str, bytes]]) -> None:
    handler, data, entry, companions = quest_lazy_context

    assert handler.supports_lazy_records()
    assert handler.get_record_count(data, entry, companions) == 19_599

    html = handler.render_data_page(data, entry, companions, page=0, page_size=25)

    assert "19,599 quests" in html
    assert "[Elvia Weekly] Gigagord" in html
    assert "Icon/Quest/Hadum08.dds" in html


def test_quest_dbss_lazy_search(quest_lazy_context: tuple[Any, bytes, PazEntry, dict[str, bytes]]) -> None:
    handler, data, entry, companions = quest_lazy_context

    assert 101 in handler.search_records(data, entry, companions, "Puzzling Words")
