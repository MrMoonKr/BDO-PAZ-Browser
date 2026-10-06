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


_ICON_DIR = "ui_texture/renewal/etc/wordmap"
_BALENOS = 0
_CALPHEON = 2
# Silver Mane Horse Crown and Golden Eagle Crown, the conquest crowns.
_SILVER_MANE_CROWN = 23381
_GOLDEN_EAGLE_CROWN = 23383

CASE = HandlerCase(
    handler_name="territoryinfo.bss",
    data_file="territoryinfo.bss",
    companion_files={},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["name", "nation"],
    internal_path="gamecommondata/binary/territoryinfo.bss",
    tests=[
        SchemaTest(
            required_keys=[
                "territory_key",
                "name_kr",
                "nation_kr",
                "name",
                "nation",
                "is_autonomous",
                "positions",
                "nation_hash",
                "icon_large_path",
                "icon_small_path",
                "crown_item_id",
                "armor_item_id",
                "crown",
                "armor",
            ],
        ),
        DeclaredCountTest(declared=header_count(offset=4)),
        TargetTest(
            col="territory_key",
            value=_BALENOS,
            expected={
                "name_kr": "발레노스 자치령",
                "nation_kr": "칼페온 공화국",
                "name": "Balenos",
                "nation": "Republic of Calpheon",
                "is_autonomous": True,
                "icon_small_path": f"{_ICON_DIR}/territorymark_valenos_small.dds",
                "crown_item_id": _SILVER_MANE_CROWN,
            },
        ),
        TargetTest(
            col="territory_key",
            value=_CALPHEON,
            expected={
                "name_kr": "칼페온 직할령",
                "name": "Calpheon",
                "is_autonomous": False,
                "crown_item_id": _GOLDEN_EAGLE_CROWN,
            },
        ),
    ],
)


@pytest.fixture(scope="module")
def territoryinfo_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_territoryinfo_bss(spec: Any, territoryinfo_result: HandlerResult) -> None:
    territoryinfo_result.check(spec)


def test_keys_follow_row_order(territoryinfo_result: HandlerResult) -> None:
    """Each key is its row index, the LOC type 12 ID."""
    keys = [r["territory_key"] for r in territoryinfo_result.records]
    assert keys == list(range(len(keys)))


def test_every_territory_has_names_and_icons(territoryinfo_result: HandlerResult) -> None:
    for record in territoryinfo_result.records:
        assert record["name_kr"] and record["nation_kr"], record["territory_key"]
        assert record["icon_large_path"].startswith("ui_texture/"), record["territory_key"]
        assert record["icon_small_path"].startswith("ui_texture/"), record["territory_key"]
        assert len(record["positions"]) == 3 and all(len(p) == 3 for p in record["positions"])


def test_nation_hash_matches_the_nation_name(territoryinfo_result: HandlerResult) -> None:
    """Territories of one nation share its hash, and no two nations do."""
    nation_by_hash: dict[int, str] = {}
    for record in territoryinfo_result.records:
        assert nation_by_hash.setdefault(record["nation_hash"], record["nation_kr"]) == record["nation_kr"]
    assert len(set(nation_by_hash.values())) == len(nation_by_hash)
