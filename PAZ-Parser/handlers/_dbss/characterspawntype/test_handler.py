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

from tests.fixtures import load_binary_fixture
from tests.runner import load_case

from _bss.stringtable.parser import GAME_SHEET, parse_key_hashes
from _dbss.characterspawntype.navi_labels import NAVI_LABELS, navi_label
from _dbss.characterspawntype.parser import SPAWN_TYPE_NAMES
from .handler import _role_column
from .role_labels import spawn_type_name


_RECORD_SIZE = 48


def _spawn_type_record(record: dict) -> dict:
    return {
        **record,
        "active_roles": [SPAWN_TYPE_NAMES[i] for i, value in enumerate(record["roles"]) if value],
    }


SPAWN_TYPE_CASE = HandlerCase(
    handler_name="characterspawntype.dbss",
    data_file="characterspawntype.dbss",
    companion_files={"characterspawntypeoffset.dbss": "characterspawntypeoffset.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Name"],
    internal_path="gamecommondata/binary/characterspawntype.dbss",
    record_mapper=_spawn_type_record,
    tests=[
        SchemaTest(required_keys=["character_id", "name", "roles", "active_roles"]),
        DeclaredCountTest(declared=header_count()),
        TargetTest(col="character_id", value=47727, expected={"name": "Jackson"}),
        # Read as a u32, this row looked like entity 82176: the NormalNpc byte
        # sat in the high half of the ID.
        TargetTest(col="character_id", value=16640, expected={"active_roles": ["NormalNpc"]}),
        TargetTest(
            col="character_id",
            value=47659,
            expected={
                "active_roles": ["ItemRepairer", "ImportantNpc", "Stable", "Intimacy", "Mating", "Grocery"],
            },
        ),
    ],
)

OFFSET_CASE = HandlerCase(
    handler_name="characterspawntypeoffset.dbss",
    data_file="characterspawntypeoffset.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/characterspawntypeoffset.dbss",
    tests=[
        SchemaTest(required_keys=["character_id", "offset", "size"]),
        DeclaredCountTest(declared=header_count(offset=4)),
        RangeTest(col="size", min_val=_RECORD_SIZE, max_val=_RECORD_SIZE),
        # The first record follows the main file's 4-byte count.
        TargetTest(col="offset", value=4, expected={"size": _RECORD_SIZE}),
    ],
)


@pytest.fixture(scope="module")
def spawn_type_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_SPAWN_TYPE_RESULT", None)
    if result is None:
        result = run_case(replace(SPAWN_TYPE_CASE, tests=[]))
        request.module._SPAWN_TYPE_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", SPAWN_TYPE_CASE.tests, ids=case_id)
def test_characterspawntype_dbss(spec: Any, spawn_type_result: HandlerResult) -> None:
    spawn_type_result.check(spec)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_characterspawntypeoffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    offset_result.check(spec)


def test_characterspawntype_role_flags_are_0_or_1(spawn_type_result: HandlerResult) -> None:
    bad = [
        record["character_id"]
        for record in spawn_type_result.records
        if any(value not in (0, 1) for value in record["roles"])
    ]
    assert not bad, f"role bytes other than 0 or 1 on characters {bad[:5]}"


def test_navi_label_hashes_match_stringtable() -> None:
    hashes = parse_key_hashes(load_binary_fixture("stringtable.bss"), GAME_SHEET)
    wrong = {
        label.key: (label.key_hash, hashes.get(label.key))
        for label in NAVI_LABELS.values()
        if hashes.get(label.key) != label.key_hash
    }
    assert not wrong, f"navi label hashes differ from stringtable.bss (stored, file): {wrong}"


def test_navi_labels_have_english_text() -> None:
    load_case(SPAWN_TYPE_CASE)
    missing = [SPAWN_TYPE_NAMES[value] for value in NAVI_LABELS if not navi_label(value)]
    assert not missing, f"navi labels without LOC text: {missing}"


def test_role_column_shows_navi_label_with_enum_tooltip() -> None:
    load_case(SPAWN_TYPE_CASE)
    stable = SPAWN_TYPE_NAMES.index("Stable")
    column = _role_column(stable, {})
    assert column.label == navi_label(stable)
    assert column.extra_attrs == f'title="Stable, SpawnType {stable}"'


def test_role_column_without_navi_label_shows_enum_name() -> None:
    guild_stable = SPAWN_TYPE_NAMES.index("GuildStable")
    assert guild_stable not in NAVI_LABELS
    assert _role_column(guild_stable, {}).label == "GuildStable"


def test_role_column_label_override_wins_over_navi_label() -> None:
    load_case(SPAWN_TYPE_CASE)
    random_shop = SPAWN_TYPE_NAMES.index("RandomShop")
    column = _role_column(random_shop, {"RandomShop": "Night Vendor"})
    assert column.label == "Night Vendor"
    assert column.extra_attrs == f'title="RandomShop, SpawnType {random_shop}"'


def test_spawn_type_name_outside_the_enum_is_the_value() -> None:
    assert spawn_type_name(len(SPAWN_TYPE_NAMES)) == str(len(SPAWN_TYPE_NAMES))
