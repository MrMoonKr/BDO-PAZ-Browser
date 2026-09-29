from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from _bss.plantexchangegroup.node_names import english_group_names
from _bss.plantexchangegroup.parser import build_production_item_index
from _bwp.waypoint.parser import neighbours, parse_waypoint_graph
from _dbss.plantzone.parser import parse_plantzone_records
from _common.lookup_index import IndexKind
from _common.pabr_offset import parse_pabr_offset_rows
from _dbss.itemsubgroup.parser import parse_itemsubgroup_records
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


_SUBGROUP_FILE = "itemsubgroup.dbss"
_SUBGROUP_OFFSET_FILE = "itemsubgroupoffset.dbss"
# Platerra Mountains lumbering: Elder Tree Timber, Bloody Tree Knot, Elder Tree Sap.
_LUMBERING_KEY = 1928
_LUMBERING_ITEMS = (4611, 5005, 5014)

CASE = HandlerCase(
    handler_name="plantexchangegroup.bss",
    data_file="plantexchangegroup.bss",
    companion_files={
        name: name for name in ("plantzone.dbss", "plantzoneoffset.dbss", "mapdata_realexplore2.bwp")
    },
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Name", "Items"],
    internal_path="gamecommondata/binary/plantexchangegroup.bss",
    lookup_indexes={IndexKind.PRODUCTION_ITEMS: {_LUMBERING_KEY: _LUMBERING_ITEMS}},
    tests=[
        SchemaTest(
            required_keys=[
                "production_key",
                "unknown_02",
                "unknown_04",
                "item_subgroup_key",
                "name_kr",
                "name_en",
                "name",
                "item_keys",
                "items",
            ],
        ),
        DeclaredCountTest(declared=header_count(offset=4)),
        TargetTest(
            col="production_key",
            value=_LUMBERING_KEY,
            expected={
                "item_subgroup_key": 42356,
                "name_kr": "플라테르 산맥 - 벌목",
                "name_en": "Platerra Mountains - Lumbering",
                "name": "Platerra Mountains - Lumbering",
                "item_keys": list(_LUMBERING_ITEMS),
                "items": ["Elder Tree Timber", "Bloody Tree Knot", "Elder Tree Sap"],
            },
        ),
        # The zone's worldmap link names the parent: Arehaza, not the Areha Palm
        # Forest of its manager family.
        TargetTest(col="production_key", value=992, expected={"name_en": "Arehaza - Specialties"}),
        # Godu Village has no main node in exploration.bss, only the link.
        TargetTest(col="production_key", value=1880, expected={"name_en": "Godu Village - Farming"}),
        # Pohalam Farm teff; not in the installed index, so no items.
        TargetTest(
            col="production_key",
            value=1539,
            expected={"item_subgroup_key": 40189, "name_kr": "포할람 농장 - 테프", "item_keys": None},
        ),
    ],
)


@pytest.fixture(scope="module")
def plantexchangegroup_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_plantexchangegroup_bss(spec: Any, plantexchangegroup_result: HandlerResult) -> None:
    plantexchangegroup_result.check(spec)


def test_every_zone_links_to_one_parent(plantexchangegroup_result: HandlerResult) -> None:
    """The English names rest on this: a production zone's only worldmap link is its parent."""
    source = plantexchangegroup_result.source
    links = neighbours(parse_waypoint_graph(source.file("mapdata_realexplore2.bwp")))
    zones = parse_plantzone_records(source.file("plantzone.dbss"), source.file("plantzoneoffset.dbss"))
    assert [zone["record_id"] for zone in zones if len(links.get(zone["record_id"], ())) != 1] == []


def test_name_is_english_or_the_korean_label(plantexchangegroup_result: HandlerResult) -> None:
    for record in plantexchangegroup_result.records:
        assert record["name"] == (record["name_en"] or record["name_kr"])


_NODE_NAMES = {1: "Town", 2: "Farm", 3: "Mine", 4: "Other Town"}


def _names(zones: list[tuple[int, int]], links: dict[int, set[int]]) -> dict[int, str]:
    return english_group_names(
        [{"record_id": zone, "production_key": key} for zone, key in zones],
        {key: frozenset(linked) for key, linked in links.items()},
        lambda key: _NODE_NAMES.get(key, ""),
    )


def test_group_name_joins_the_linked_parent_and_the_zone() -> None:
    assert _names([(2, 100), (3, 101)], {2: {1}, 3: {1}}) == {100: "Town - Farm", 101: "Town - Mine"}


def test_group_name_needs_one_name_across_its_zones() -> None:
    # Two zones under different parents: no single name.
    assert _names([(2, 100), (3, 100)], {2: {1}, 3: {4}}) == {}
    # One zone of the key has no name, so the other does not decide alone.
    assert _names([(2, 100), (9, 100)], {2: {1}, 9: {1}}) == {}


def test_group_name_needs_a_single_link() -> None:
    for links in ({}, {2: {1, 4}}):
        assert _names([(2, 100)], links) == {}


def test_production_item_index_matches_the_subgroup_table(
    plantexchangegroup_result: HandlerResult,
) -> None:
    """Each production key maps to its subgroup's items, or is left out when the subgroup is missing."""
    from tests.fixtures import ensure_fixtures

    paths = ensure_fixtures(replace(
        CASE,
        companion_files={name: name for name in (_SUBGROUP_FILE, _SUBGROUP_OFFSET_FILE)},
    ))
    subgroups = paths[_SUBGROUP_FILE].read_bytes()
    offsets = paths[_SUBGROUP_OFFSET_FILE].read_bytes()
    index = build_production_item_index(plantexchangegroup_result.source.data, subgroups, offsets)

    indexed_subgroups = {row.entry_id for row in parse_pabr_offset_rows(offsets)}
    items_by_subgroup = {
        subgroup.subgroup_key: subgroup.item_keys
        for subgroup in parse_itemsubgroup_records(subgroups, offsets)
    }
    expected = {
        record["production_key"]: items_by_subgroup[record["item_subgroup_key"]]
        for record in plantexchangegroup_result.records
        if record["item_subgroup_key"] in indexed_subgroups
    }
    assert index == expected
    assert index[_LUMBERING_KEY] == _LUMBERING_ITEMS
