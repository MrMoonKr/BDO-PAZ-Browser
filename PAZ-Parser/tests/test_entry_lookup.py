"""The folder tree and the case-insensitive entry lookup."""
from __future__ import annotations

from api.bdo_api import Api
from api.bdo_api_helpers import fold_entry_map
from api.bdo_tree import build_tree
from bdo_models import PazEntry


def _entry(path: str) -> PazEntry:
    return PazEntry("PAD00001.PAZ", path, 0, 1, 1, 0, 0)


_ENTRIES = [
    _entry("gamecommondata/binary/quest.dbss"),
    _entry("readme.txt"),
    _entry("gamecommondata/binary/skill.dbss"),
    _entry("gamecommondata/item.xml"),
    _entry("ui_texture/icon/Old/Pet.dds"),
]


def _api() -> Api:
    api = Api()
    api._entry_map = {entry.internal_path: entry for entry in _ENTRIES}
    api._entry_map_folded = fold_entry_map(api._entry_map)
    return api


def test_the_tree_nests_folders_and_keeps_root_files() -> None:
    tree = build_tree(_ENTRIES)

    assert set(tree) == {"gamecommondata", "readme.txt", "ui_texture"}
    assert tree["readme.txt"] is _ENTRIES[1]
    assert set(tree["gamecommondata"]) == {"binary", "item.xml"}
    assert tree["gamecommondata"]["binary"] == {"quest.dbss": _ENTRIES[0], "skill.dbss": _ENTRIES[2]}
    assert tree["ui_texture"]["icon"]["Old"] == {"Pet.dds": _ENTRIES[4]}


def test_the_tree_normalises_backslashes() -> None:
    entry = _entry("ui\\icon.dds")

    assert build_tree([entry]) == {"ui": {"icon.dds": entry}}


def test_a_lowercase_path_is_found_in_any_case() -> None:
    api = _api()

    assert api._entry_ignoring_case("GameCommonData/Binary/Quest.dbss") is _ENTRIES[0]


def test_a_mixed_case_path_is_found_in_any_case() -> None:
    api = _api()

    assert api._entry_ignoring_case("ui_texture/icon/old/pet.dds") is _ENTRIES[4]
    assert api._entry_ignoring_case("UI_TEXTURE/ICON/OLD/PET.DDS") is _ENTRIES[4]


def test_only_paths_that_are_not_lowercase_are_folded() -> None:
    entry_map = {entry.internal_path: entry for entry in _ENTRIES}

    assert fold_entry_map(entry_map) == {"ui_texture/icon/old/pet.dds": _ENTRIES[4]}


def test_an_unknown_path_is_none() -> None:
    assert _api()._entry_ignoring_case("gamecommondata/binary/buff.dbss") is None
