from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

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


_ALL_BASE_SPECIES = [0, 1, 2, 3, 4, 5]

PLANTZONE_CASE = HandlerCase(
    handler_name="plantzone.dbss",
    data_file="plantzone.dbss",
    companion_files={"plantzoneoffset.dbss": "plantzoneoffset.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Node Name"],
    internal_path="gamecommondata/binary/plantzone.dbss",
    tests=[
        SchemaTest(
            required_keys=[
                "record_id",
                "node_name",
                "unknown_0e",
                "production_key",
                "unknown_19",
                "worker_species",
                "worker_species_text",
                "data_size",
            ]
        ),
        CountTest(expected=394),
        RangeTest(col="unknown_0e", min_val=0, max_val=4),
        PosTest(
            pos=0,
            expected={
                "record_id": 1030,
                "node_name": "Fish Drying Yard 2",
                "unknown_0e": 4,
                "production_key": 2017,
                "unknown_19": 0,
                "worker_species": _ALL_BASE_SPECIES,
                "worker_species_text": "Goblin, Human, Giant, Papu, Fadus, Dwarf",
            },
        ),
        PosTest(pos=-1, expected={"record_id": 405, "unknown_0e": 4, "production_key": 914, "data_size": 37}),
        # Dokkebi Forest excavation takes Dokkebi workers only.
        TargetTest(
            col="record_id",
            value=1807,
            expected={"worker_species": [6], "worker_species_text": "Dokkebi", "data_size": 32},
        ),
        # Balenos Specialties farms count unknown_19 up from 1 to 7.
        TargetTest(
            col="record_id",
            value=110,
            expected={"production_key": 977, "unknown_19": 7},
        ),
    ],
)

OFFSET_CASE = HandlerCase(
    handler_name="plantzoneoffset.dbss",
    data_file="plantzoneoffset.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/plantzoneoffset.dbss",
    tests=[
        SchemaTest(required_keys=["record_id", "data_offset", "data_size"]),
        CountTest(expected=394),
        PosTest(pos=0, expected={"record_id": 1030, "data_offset": 8304, "data_size": 37}),
        PosTest(pos=-1, expected={"record_id": 405, "data_offset": 14335, "data_size": 37}),
    ],
)


@pytest.fixture(scope="module")
def plantzone_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_PLANTZONE_RESULT", None)
    if result is None:
        result = run_case(replace(PLANTZONE_CASE, tests=[]))
        request.module._PLANTZONE_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", PLANTZONE_CASE.tests, ids=case_id)
def test_plantzone_dbss(spec: Any, plantzone_result: HandlerResult) -> None:
    plantzone_result.check(spec)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_plantzoneoffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    offset_result.check(spec)
