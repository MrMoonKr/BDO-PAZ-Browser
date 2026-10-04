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

from _common.worker import (
    LUCK_SCALE,
    MOVE_SPEED_SCALE,
    WORK_SPEED_SCALE,
    WorkerGrade,
    format_stat,
    worker_grade,
    worker_name_cell,
)


_ICON_FOLDER = "New_UI_Common_forLua/Widget/WorldMap/WorkerIcon/"

CASE = HandlerCase(
    handler_name="plantworker.bss",
    data_file="plantworker.bss",
    companion_files={},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Name"],
    internal_path="gamecommondata/binary/plantworker.bss",
    tests=[
        SchemaTest(
            required_keys=[
                "slot",
                "worker_id",
                "next_worker_id",
                "name",
                "worker_grade",
                "grade_class",
                "unknown_0a",
                "move_speed",
                "stamina",
                "luck",
                "icon_index",
                "icon_path",
                "base_work_speed",
            ],
        ),
        DeclaredCountTest(declared=header_count(offset=4)),
        TargetTest(
            col="worker_id",
            value=8047,
            expected={
                "name": "Dokkebi Worker",
                "worker_grade": WorkerGrade.BASE,
                "next_worker_id": 8048,
                "icon_path": f"{_ICON_FOLDER}Morning_Dokev01.dds",
            },
        ),
        TargetTest(
            col="worker_id",
            value=7502,
            expected={
                "name": "Giant Worker",
                "next_worker_id": 7551,
                "icon_path": f"{_ICON_FOLDER}Worker_Giant01.dds",
            },
        ),
        TargetTest(
            col="worker_id",
            value=7504,
            expected={
                "name": "Goblin Worker",
                "next_worker_id": 7552,
                "icon_path": f"{_ICON_FOLDER}Worker_Goblin01.dds",
            },
        ),
        # Named workers have their own grade class; the game shows them yellow.
        TargetTest(col="worker_id", value=7614, expected={"name": "Acher", "worker_grade": WorkerGrade.NAMED}),
        TargetTest(col="worker_id", value=8045, expected={"name": "Torres", "worker_grade": WorkerGrade.ARTISAN}),
        TargetTest(col="worker_id", value=7501, expected={"worker_grade": WorkerGrade.NAIVE}),
        TargetTest(col="worker_id", value=8000, expected={"worker_grade": WorkerGrade.NAIVE}),
    ],
)


@pytest.fixture(scope="module")
def plantworker_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_plantworker_bss(spec: Any, plantworker_result: HandlerResult) -> None:
    plantworker_result.check(spec)


@pytest.mark.parametrize(
    ("grade_class", "worker_id", "name", "grade"),
    [
        (28023, 7501, "Naive Worker", WorkerGrade.NAIVE),
        (28023, 7504, "Goblin Worker", WorkerGrade.BASE),
        (28023, 8000, "QA Super Worker", WorkerGrade.NAIVE),
        (28024, 8007, "Demibeast Worker", WorkerGrade.NAIVE),
        (28024, 8013, "Skilled Papu Worker", WorkerGrade.SKILLED),
        (28025, 8008, "Demibeast Professional Worker", WorkerGrade.PROFESSIONAL),
        (28026, 8045, "Torres", WorkerGrade.ARTISAN),
        (28027, 7614, "Acher", WorkerGrade.NAMED),
        (28027, 7614, "", WorkerGrade.NAMED),
        (1, 7614, "Acher", None),
        (None, 7614, "Acher", None),
    ],
)
def test_worker_grade_from_class(
    grade_class: int | None, worker_id: int, name: str, grade: WorkerGrade | None
) -> None:
    assert worker_grade(grade_class, worker_id, name) == grade


def test_worker_name_cell_colors_by_grade() -> None:
    assert worker_name_cell("Artisan Goblin Worker", WorkerGrade.ARTISAN) == (
        '<span class="worker-grade-4">Artisan Goblin Worker</span>'
    )
    assert worker_name_cell("Tiny <Nose>", None) == "Tiny &lt;Nose&gt;"
    assert worker_name_cell(None, None) == "-"


def test_format_stat_uses_the_in_game_scales() -> None:
    # A base Giant Worker as stored: work speed 30.00, move speed 2.00, luck 5.00 in game.
    assert format_stat(30_000_000, WORK_SPEED_SCALE) == "30.00"
    assert format_stat(200, MOVE_SPEED_SCALE) == "2.00"
    assert format_stat(50_000, LUCK_SCALE) == "5.00"
    assert format_stat(None, LUCK_SCALE) == "-"
