from __future__ import annotations

import pickle
from pathlib import Path

import paz.bdo_index_cache as index_cache
from paz.bdo_index_cache import load_index_cache, save_index_cache

_INDEXES = {
    "character_icon": {2053: "ui_texture/icon/new_icon/03_etc/06_housing/00058003.dds"},
    "character_item": {2053: 58011},
}


def test_cache_round_trips_with_the_same_fingerprint(tmp_path: Path) -> None:
    save_index_cache(tmp_path, 7, "abc", _INDEXES)

    assert load_index_cache(tmp_path, "abc") == (7, _INDEXES)


def test_cache_built_by_other_code_is_ignored(tmp_path: Path) -> None:
    save_index_cache(tmp_path, 7, "abc", _INDEXES)

    assert load_index_cache(tmp_path, "def") is None


def test_cache_from_before_fingerprints_is_ignored(tmp_path: Path) -> None:
    with (tmp_path / index_cache._CACHE_FILE).open("wb") as f:
        pickle.dump({"format": 2, "version": 7, "indexes": _INDEXES}, f)

    assert load_index_cache(tmp_path, "abc") is None


def test_saving_removes_the_legacy_icon_cache(tmp_path: Path) -> None:
    legacy = tmp_path / index_cache._LEGACY_CACHE_FILE
    legacy.write_bytes(b"old")

    save_index_cache(tmp_path, 7, "abc", _INDEXES)

    assert not legacy.exists()
