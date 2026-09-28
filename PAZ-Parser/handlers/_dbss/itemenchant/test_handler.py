from __future__ import annotations

import struct
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


_ICON_ROOT = "ui_texture/icon/new_icon"
# King Clam Wall Ornament: furniture, so its icon is named after the 3D asset
# and is unreachable from the item ID alone. It is the case this format solves.
_KING_CLAM = 24626
# [Event] Fence places character 2053, which has no icon of its own.
_EVENT_FENCE = 58011
_EVENT_FENCE_CHARACTER = 2053
_WEAPON = 697192
# The key packs the item ID into its low 24 bits and the key variant above them.
_MAX_ITEM_ID = 0xFFFFFF
_OFFSET_HEADER_SIZE = 8
_OFFSET_ROW_SIZE = 12
_KEY_VARIANT_SHIFT = 24

CASE = HandlerCase(
    handler_name="itemenchant.dbss",
    data_file="itemenchant.dbss",
    companion_files={"itemenchantoffset.dbss": "itemenchantoffset.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Item"],
    internal_path="gamecommondata/binary/itemenchant.dbss",
    tests=[
        SchemaTest(
            required_keys=[
                "item_id",
                "key_variant",
                "icon_path",
                "effect_tag",
                "block_size",
                "item_name",
                "character_id",
                "character_name",
            ],
        ),
        DeclaredCountTest(declared=header_count()),
        RangeTest(col="item_id", min_val=1, max_val=_MAX_ITEM_ID),
        # The furniture case: icon path comes from the block, not the item ID.
        TargetTest(
            col="item_id",
            value=_KING_CLAM,
            expected={
                "key_variant": 0,
                "item_name": "King Clam Wall Ornament",
                "icon_path": (
                    f"{_ICON_ROOT}/03_etc/06_housing/"
                    "inhouse_cultivate_sea_clam_01_wall.dds"
                ),
                "effect_tag": "",
                "character_id": 17026,
                "character_name": "King Clam Wall Ornament",
            },
        ),
        TargetTest(
            col="item_id",
            value=_EVENT_FENCE,
            expected={
                "key_variant": 0,
                "character_id": _EVENT_FENCE_CHARACTER,
                "character_name": "[Event] Fence",
            },
        ),
        # A weapon places no character; stored as None so it sorts last.
        TargetTest(
            col="item_id",
            value=_WEAPON,
            expected={"character_id": None, "character_name": ""},
        ),
    ],
)


@pytest.fixture(scope="module")
def itemenchant_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_HANDLER_RESULT", None)
    if result is None:
        result = run_case(replace(CASE, tests=[]))
        request.module._HANDLER_RESULT = result
    return result


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_itemenchant_dbss(
    spec: Any,
    itemenchant_result: HandlerResult,
) -> None:
    itemenchant_result.check(spec)


def test_build_item_icon_index_covers_the_furniture_case() -> None:
    """The index is what lets an item ID reach an asset-named icon."""
    from _dbss.itemenchant.parser import build_item_icon_index
    from tests.fixtures import ensure_fixtures

    paths = ensure_fixtures(CASE)
    index = build_item_icon_index(
        paths["itemenchant.dbss"].read_bytes(),
        paths["itemenchantoffset.dbss"].read_bytes(),
    )

    # One entry per variant-0 record, not one per key variant.
    offsets = paths["itemenchantoffset.dbss"].read_bytes()
    (count,) = struct.unpack_from("<I", offsets, 4)
    base_items = sum(
        1
        for row in range(count)
        if not struct.unpack_from("<I", offsets, _OFFSET_HEADER_SIZE + row * _OFFSET_ROW_SIZE)[0]
        >> _KEY_VARIANT_SHIFT
    )
    assert len(index) == base_items
    assert index[_KING_CLAM] == (
        f"{_ICON_ROOT}/03_etc/06_housing/"
        "inhouse_cultivate_sea_clam_01_wall.dds"
    )
    # Every path stays inside the icon tree.
    assert all(p.startswith("ui_texture/icon/") for p in index.values())


def test_build_character_item_index_links_placed_objects_and_pets() -> None:
    from _dbss.itemenchant.parser import build_character_item_index
    from tests.fixtures import ensure_fixtures

    paths = ensure_fixtures(CASE)
    index = build_character_item_index(
        paths["itemenchant.dbss"].read_bytes(),
        paths["itemenchantoffset.dbss"].read_bytes(),
    )

    # A kept character is named by exactly one item, so no item appears twice.
    assert len(set(index.values())) == len(index)
    assert 0 not in index
    assert index[_EVENT_FENCE_CHARACTER] == _EVENT_FENCE
    # [Pet] Striped Cat (Tier 3) summons character 9425, "Cat".
    assert index[9425] == 860014
    # Named by 120 unrelated items, so it is not a link and is left out.
    assert 1 not in index
