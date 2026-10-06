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

from .parser import parse_regiongroupinfo_records


CASE = HandlerCase(
    handler_name="regiongroupinfo.bss",
    data_file="regiongroupinfo.bss",
    companion_files={},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["NodeName"],
    internal_path="gamecommondata/binary/regiongroupinfo.bss",
    tests=[
        SchemaTest(
            required_keys=[
                "region_group_key",
                "node_key",
                "node_name",
                "pos_x",
                "pos_y",
                "pos_z",
                "unknown_03",
                "unknown_09",
                "unknown_0a",
                "unknown_0b",
                "unknown_19",
                "unknown_1d",
                "unknown_21",
                "unknown_31",
            ],
        ),
        DeclaredCountTest(declared=header_count(offset=4)),
        RangeTest(col="unknown_09", min_val=0, max_val=1),
        RangeTest(col="unknown_0a", min_val=0, max_val=1),
        RangeTest(col="unknown_0b", min_val=0, max_val=1),
        # Each group names the node of its main town.
        TargetTest(col="region_group_key", value=1, expected={"node_key": 1, "node_name": "Velia"}),
        TargetTest(col="region_group_key", value=31, expected={"node_key": 601, "node_name": "Calpheon"}),
        TargetTest(col="region_group_key", value=202, expected={"node_key": 1301, "node_name": "Valencia City"}),
    ],
)


@pytest.fixture(scope="module")
def regiongroupinfo_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_regiongroupinfo_bss(spec: Any, regiongroupinfo_result: HandlerResult) -> None:
    regiongroupinfo_result.check(spec)


def test_region_group_keys_are_unique(regiongroupinfo_result: HandlerResult) -> None:
    keys = [record["region_group_key"] for record in regiongroupinfo_result.records]
    assert len(keys) == len(set(keys))


def test_group_without_node_has_no_name(regiongroupinfo_result: HandlerResult) -> None:
    unnamed = [r for r in regiongroupinfo_result.records if r["node_key"] is None]
    assert unnamed, "expected at least one group without a node"
    assert all(r["node_name"] == "" for r in unnamed)


def test_rows_that_miss_the_string_table_are_rejected() -> None:
    # PABR, 1 row declared, but the trailer puts the string table right after the header.
    data = b"PABR" + (1).to_bytes(4, "little") + bytes(51) + (0).to_bytes(4, "little")
    data += (8).to_bytes(4, "little") + bytes(4)
    with pytest.raises(ValueError, match="string table starts"):
        parse_regiongroupinfo_records(data)
