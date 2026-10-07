from __future__ import annotations

import pickle
from pathlib import Path

import paz.bdo_index_cache as index_cache
from paz.bdo_index_cache import IndexCacheData, index_digests, load_index_cache, save_index_cache

_INDEXES = {
    "character_icon": {2053: "ui_texture/icon/new_icon/03_etc/06_housing/00058003.dds"},
    "character_item": {2053: 58011},
}
_DATA = IndexCacheData(7, _INDEXES, index_digests(_INDEXES))


def test_cache_round_trips_with_the_same_fingerprint(tmp_path: Path) -> None:
    save_index_cache(tmp_path, "abc", _DATA)

    assert load_index_cache(tmp_path, "abc") == _DATA


def test_cache_built_by_other_code_is_ignored(tmp_path: Path) -> None:
    save_index_cache(tmp_path, "abc", _DATA)

    assert load_index_cache(tmp_path, "def") is None


def test_cache_from_before_fingerprints_is_ignored(tmp_path: Path) -> None:
    with (tmp_path / index_cache.CACHE_FILE).open("wb") as f:
        pickle.dump({"format": 2, "version": 7, "indexes": _INDEXES}, f)

    assert load_index_cache(tmp_path, "abc") is None


def test_digests_change_only_with_the_index_content() -> None:
    changed = {**_INDEXES, "character_item": {2053: 58012}}

    before = index_digests(_INDEXES)
    after = index_digests(changed)

    assert after["character_icon"] == before["character_icon"]
    assert after["character_item"] != before["character_item"]
