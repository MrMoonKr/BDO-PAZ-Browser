from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from _common.pabr_offset import parse_pabr_offset_rows
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


_OFFSET_FILE = "itemsubgroupoffset.dbss"
# The records start right after the u32 record_count.
_COUNT_SIZE = 4
# Keys are u16 in the offset table; a subgroup never has zero entries.
_MAX_SUBGROUP_KEY = 0xFFFF
_MAX_ENTRIES = 0xFFFFFFFF
# Red Coral Earring at enchant level 4: (4 << 24) | 11817.
_RED_CORAL_EARRING_4 = (4 << 24) | 11817

CASE = HandlerCase(
    handler_name="itemsubgroup.dbss",
    data_file="itemsubgroup.dbss",
    companion_files={_OFFSET_FILE: _OFFSET_FILE},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Item Names"],
    internal_path="gamecommondata/binary/itemsubgroup.dbss",
    tests=[
        SchemaTest(required_keys=["subgroup_key", "entry_count", "item_keys", "items"]),
        DeclaredCountTest(declared=header_count(offset=0)),
        RangeTest(col="subgroup_key", min_val=0, max_val=_MAX_SUBGROUP_KEY),
        RangeTest(col="entry_count", min_val=1, max_val=_MAX_ENTRIES),
        # Platerra Mountains lumbering, the worker production example.
        TargetTest(
            col="subgroup_key",
            value=42356,
            expected={
                "item_keys": [4611, 5005, 5014],
                "items": ["Elder Tree Timber", "Bloody Tree Knot", "Elder Tree Sap"],
            },
        ),
        # An entry above enchant level 0 shows the level after the name.
        TargetTest(
            col="subgroup_key",
            value=48320,
            expected={
                "item_keys": [_RED_CORAL_EARRING_4],
                "items": ["Red Coral Earring (4)"],
            },
        ),
    ],
)

OFFSET_CASE = HandlerCase(
    handler_name=_OFFSET_FILE,
    data_file=_OFFSET_FILE,
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path=f"gamecommondata/binary/{_OFFSET_FILE}",
    tests=[
        SchemaTest(required_keys=["subgroup_key", "offset", "size"]),
        DeclaredCountTest(declared=header_count(offset=4)),
        RangeTest(col="subgroup_key", min_val=0, max_val=_MAX_SUBGROUP_KEY),
    ],
)


@pytest.fixture(scope="module")
def itemsubgroup_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_itemsubgroup_dbss(spec: Any, itemsubgroup_result: HandlerResult) -> None:
    itemsubgroup_result.check(spec)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_itemsubgroupoffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    offset_result.check(spec)


def test_records_fill_the_file(itemsubgroup_result: HandlerResult) -> None:
    """Sorted by offset, the records cover every byte after the count, with no gaps."""
    source = itemsubgroup_result.source
    rows = sorted(parse_pabr_offset_rows(source.file(_OFFSET_FILE)), key=lambda row: row.offset)
    position = _COUNT_SIZE
    for row in rows:
        assert row.offset == position, f"gap or overlap before subgroup {row.entry_id}"
        position += row.size
    assert position == len(source.data)
