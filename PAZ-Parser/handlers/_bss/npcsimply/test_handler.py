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
    UserLanguageTest,
    case_id,
    header_count,
    run_case,
)
from tests.runner import load_case

from _bss.npcsimply.leases import character_leases
from _common.loc import LOC_NULL
from _common.lookup_index import IndexKind, init_index
from _dbss.characterspawntype.navi_labels import navi_label
from _dbss.characterspawntype.parser import ROLE_COUNT
from _dbss.characterspawntype.role_labels import role_label_overrides
from _dbss.detail_dialog.lease import Lease


# unknown_12 reads 0xFFFF on every row without a lease item.
_NO_LEASE_ITEM = 0xFFFF

CASE = HandlerCase(
    handler_name="npcsimply.bss",
    data_file="npcsimply.bss",
    companion_files={},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Name", "Role"],
    internal_path="gamecommondata/binary/npcsimply.bss",
    tests=[
        SchemaTest(
            required_keys=[
                "character_id",
                "name",
                "kind",
                "kind_name",
                "kind_label",
                "name_kr",
                "role_kr",
                "role",
                "script",
                "knowledge_id",
                "unknown_02",
                "lease_item_id",
                "leases",
                "lease_count",
                "lease_cost",
                "unknown_12",
                "has_lease_condition",
            ],
        ),
        DeclaredCountTest(declared=header_count(offset=4)),
        RangeTest(col="kind", min_val=0, max_val=ROLE_COUNT - 1),
        # LOC type 6 names and titles every NPC in this file.
        UserLanguageTest(fields=["name", "role"]),
        RangeTest(col="has_lease_condition", min_val=0, max_val=1),
        TargetTest(
            col="character_id",
            value=47791,
            expected={
                "kind": 4,
                "kind_name": "ImportantNpc",
                "name_kr": "에론",
                "role_kr": "<거점 관리인>",
                "script": "getknowledge(15936);",
                "knowledge_id": 15936,
            },
        ),
        # No action script: the empty pool string, so no knowledge ID.
        TargetTest(
            col="character_id",
            value=47727,
            expected={
                "name": "Jackson",
                "kind_name": "ShopMerchant",
                "name_kr": "잭슨",
                "role_kr": "<과일상인>",
                # LOC type 6 field 1, the user-language title.
                "role": "<Fruit Vendor>",
                "script": "",
                "knowledge_id": None,
            },
        ),
        TargetTest(
            col="character_id",
            value=47647,
            expected={
                "name": "Neoksam",
                "kind": 25,
                "kind_name": "ItemMarket",
                "role_kr": "<거래소장>",
                "knowledge_id": 2387,
            },
        ),
        # Storage Keeper who leases the [CP] Container (item 3001), checked in game.
        TargetTest(
            col="character_id",
            value=47008,
            # Her lease checks that you do not own a Container yet.
            expected={"name": "Delorence", "lease_item_id": 3001, "has_lease_condition": 1},
        ),
        # The only script spelled `getKnowledge`.
        TargetTest(
            col="character_id",
            value=50613,
            expected={"script": "getKnowledge(933);", "knowledge_id": 933},
        ),
    ],
)


@pytest.fixture(scope="module")
def npcsimply_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_npcsimply_bss(spec: Any, npcsimply_result: HandlerResult) -> None:
    npcsimply_result.check(spec)


def test_npcsimply_unknown_12_marks_rows_without_lease_item(npcsimply_result: HandlerResult) -> None:
    mismatched = [
        record["character_id"]
        for record in npcsimply_result.records
        if (record["unknown_12"] == _NO_LEASE_ITEM) != (record["lease_item_id"] is None)
    ]
    assert not mismatched, f"unknown_12 and lease_item_id disagree on characters {mismatched[:5]}"


def test_npcsimply_every_kind_has_an_english_label(npcsimply_result: HandlerResult) -> None:
    load_case(CASE)
    overrides = role_label_overrides("en")
    unlabelled = sorted({
        r["kind_name"]
        for r in npcsimply_result.records
        if not (overrides.get(r["kind_name"]) or navi_label(r["kind"]))
    })
    assert not unlabelled, f"kinds without a navi label or override: {unlabelled}"


def test_character_leases_keeps_the_stored_cost() -> None:
    """Dialog leases come from the index; the lease stored in npcsimply wins on cost."""
    init_index(IndexKind.CHARACTER_LEASES, {7: (100, 1, 200, 5)})
    try:
        assert character_leases(7, 100, 2) == [Lease(100, 2), Lease(200, 5)]
        assert character_leases(7, 300, 4) == [Lease(300, 4), Lease(100, 1), Lease(200, 5)]
        assert character_leases(7, 0, 0) == [Lease(100, 1), Lease(200, 5)]
        assert character_leases(8, 0, 0) == []
    finally:
        init_index(IndexKind.CHARACTER_LEASES, None)
    # Without the index only the stored lease is known.
    assert character_leases(7, 100, 2) == [Lease(100, 2)]


def test_npcsimply_loc_null_title_reads_as_no_role(npcsimply_result: HandlerResult) -> None:
    """LOC keeps `<null>` for a character without a title; the role stays empty."""
    nulls = [record["character_id"] for record in npcsimply_result.records if record["role"] == LOC_NULL]
    assert not nulls, f"<null> shown as a role on characters {nulls[:5]}"
