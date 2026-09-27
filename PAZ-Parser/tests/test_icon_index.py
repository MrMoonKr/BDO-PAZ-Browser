from __future__ import annotations

import pytest

from _common.icon_index import (
    ITEM_ICON_DIR,
    IconKind,
    clear_icon_indexes,
    derive_icon_path,
    icon_index_size,
    icon_path,
    init_icon_index,
    is_icon_index_loaded,
)

_KING_CLAM = 24626
_SWEET_HONEY_WINE = 54030
_FURNITURE_ICON = (
    "ui_texture/icon/new_icon/03_etc/06_housing/"
    "inhouse_cultivate_sea_clam_01_wall.dds"
)


@pytest.fixture(autouse=True)
def _clear_indexes():
    clear_icon_indexes()
    yield
    clear_icon_indexes()


def test_derives_from_id_when_no_index_loaded() -> None:
    assert not is_icon_index_loaded(IconKind.ITEM)
    assert icon_path(IconKind.ITEM, _SWEET_HONEY_WINE) == (
        f"{ITEM_ICON_DIR}/00054030.png"
    )


def test_index_entry_wins_over_derivation() -> None:
    init_icon_index(IconKind.ITEM, {_KING_CLAM: _FURNITURE_ICON})

    assert is_icon_index_loaded(IconKind.ITEM)
    assert icon_index_size(IconKind.ITEM) == 1
    # The furniture case: derivation cannot reach this path.
    assert icon_path(IconKind.ITEM, _KING_CLAM) == _FURNITURE_ICON
    assert derive_icon_path(IconKind.ITEM, _KING_CLAM) != _FURNITURE_ICON


def test_falls_back_when_index_lacks_the_entity() -> None:
    init_icon_index(IconKind.ITEM, {_KING_CLAM: _FURNITURE_ICON})

    assert icon_path(IconKind.ITEM, _SWEET_HONEY_WINE) == (
        f"{ITEM_ICON_DIR}/00054030.png"
    )


def test_clearing_one_kind_restores_derivation() -> None:
    init_icon_index(IconKind.ITEM, {_KING_CLAM: _FURNITURE_ICON})
    init_icon_index(IconKind.ITEM, None)

    assert not is_icon_index_loaded(IconKind.ITEM)
    assert icon_path(IconKind.ITEM, _KING_CLAM) == f"{ITEM_ICON_DIR}/00024626.png"


def test_clear_all_drops_every_kind() -> None:
    init_icon_index(IconKind.ITEM, {_KING_CLAM: _FURNITURE_ICON})
    clear_icon_indexes()

    assert not is_icon_index_loaded(IconKind.ITEM)
    assert icon_index_size(IconKind.ITEM) == 0


def test_empty_index_still_counts_as_loaded() -> None:
    init_icon_index(IconKind.ITEM, {})

    assert is_icon_index_loaded(IconKind.ITEM)
    assert icon_index_size(IconKind.ITEM) == 0
    assert icon_path(IconKind.ITEM, _KING_CLAM) == f"{ITEM_ICON_DIR}/00024626.png"


def test_kinds_without_a_deriver_return_empty() -> None:
    """Quest and character icons are asset-named far more often than ID-named,
    so guessing a path would be wrong more often than right."""
    assert derive_icon_path(IconKind.QUEST, 795132) == ""
    assert derive_icon_path(IconKind.CHARACTER, 16111) == ""
    assert icon_path(IconKind.QUEST, 795132) == ""


def test_indexed_kinds_without_a_deriver_still_resolve() -> None:
    init_icon_index(IconKind.QUEST, {795132: "ui_texture/icon/quest/8700_12.dds"})

    assert icon_path(IconKind.QUEST, 795132) == "ui_texture/icon/quest/8700_12.dds"
    assert icon_path(IconKind.QUEST, 1) == ""


def test_kinds_are_isolated_from_each_other() -> None:
    init_icon_index(IconKind.ITEM, {_KING_CLAM: _FURNITURE_ICON})
    init_icon_index(IconKind.QUEST, {1: "ui_texture/icon/quest/a.dds"})
    init_icon_index(IconKind.QUEST, None)

    assert is_icon_index_loaded(IconKind.ITEM)
    assert not is_icon_index_loaded(IconKind.QUEST)
    assert icon_path(IconKind.ITEM, _KING_CLAM) == _FURNITURE_ICON


def test_kind_values_are_stable_cache_keys() -> None:
    """The disk cache stores kind.value, so these must not drift casually."""
    assert IconKind.ITEM.value == "item"
    assert IconKind.QUEST.value == "quest"
    assert IconKind.CHARACTER.value == "character"
    assert len({kind.value for kind in IconKind}) == len(list(IconKind))


def test_override_file_parses_without_error() -> None:
    """A typo in the hand-edited file must be reported, not silently ignored."""
    from _common.icon_index import icon_override_error, reload_icon_overrides

    reload_icon_overrides()
    assert icon_override_error() == ""


def test_override_beats_index_and_derivation(monkeypatch) -> None:
    import _common.icon_index as module

    monkeypatch.setattr(
        module, "_OVERRIDES", {IconKind.ITEM: {_KING_CLAM: "ui_texture/icon/fixed.dds"}}
    )
    init_icon_index(IconKind.ITEM, {_KING_CLAM: _FURNITURE_ICON})

    assert icon_path(IconKind.ITEM, _KING_CLAM) == "ui_texture/icon/fixed.dds"
    # Untouched ids still fall through to the index.
    assert icon_path(IconKind.ITEM, 1) == f"{ITEM_ICON_DIR}/00000001.png"


def test_empty_override_suppresses_a_wrong_derived_path(monkeypatch) -> None:
    import _common.icon_index as module

    monkeypatch.setattr(module, "_OVERRIDES", {IconKind.ITEM: {9: ""}})

    # Item 9 derives to a path that is not shipped; "" says so explicitly.
    assert icon_path(IconKind.ITEM, 9) == ""


_FENCE_CHARACTER = 2053
_FENCE_ITEM = 58011
_FENCE_ICON = "ui_texture/icon/new_icon/03_etc/06_housing/00058003.dds"


def _borrow(own: dict[int, str], shipped: set[str]) -> dict[int, str]:
    from _common.icon_index import borrow_icons

    return borrow_icons(
        own,
        {_FENCE_ITEM: _FENCE_ICON},
        {_FENCE_CHARACTER: _FENCE_ITEM},
        shipped.__contains__,
    )


def test_borrow_fills_a_character_with_no_icon() -> None:
    assert _borrow({}, {_FENCE_ICON}) == {_FENCE_CHARACTER: _FENCE_ICON}


def test_borrow_replaces_an_icon_the_client_does_not_ship() -> None:
    dead = "ui_texture/icon/new_icon/03_etc/06_housing/missing.dds"

    assert _borrow({_FENCE_CHARACTER: dead}, {_FENCE_ICON}) == {
        _FENCE_CHARACTER: _FENCE_ICON,
    }


def test_borrow_keeps_a_working_own_icon() -> None:
    own_icon = "ui_texture/icon/new_icon/03_etc/06_housing/own.dds"

    assert _borrow({_FENCE_CHARACTER: own_icon}, {own_icon, _FENCE_ICON}) == {
        _FENCE_CHARACTER: own_icon,
    }


def test_borrow_never_swaps_in_a_dead_item_icon() -> None:
    dead = "ui_texture/icon/new_icon/03_etc/06_housing/missing.dds"

    assert _borrow({_FENCE_CHARACTER: dead}, set()) == {_FENCE_CHARACTER: dead}
    assert _borrow({}, set()) == {}


def test_borrow_leaves_the_input_untouched() -> None:
    own: dict[int, str] = {}
    _borrow(own, {_FENCE_ICON})

    assert own == {}
