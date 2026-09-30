from __future__ import annotations

from pathlib import Path

from paz.bdo_thumbnail_cache import ThumbnailCache

_PATH = "ui_texture/icon/quest/morningland_boss_03_02_full.dds"
_URL = "data:image/png;base64,AAAA"


def test_thumbnail_survives_a_reopen_on_the_same_version(tmp_path: Path) -> None:
    cache = ThumbnailCache(tmp_path, 3458)
    cache.put(_PATH, _URL)
    cache.close()

    reopened = ThumbnailCache(tmp_path, 3458)

    assert reopened.get(_PATH) == _URL
    assert reopened.error == ""
    reopened.close()


def test_a_new_client_version_clears_the_store(tmp_path: Path) -> None:
    cache = ThumbnailCache(tmp_path, 3458)
    cache.put(_PATH, _URL)
    cache.close()

    patched = ThumbnailCache(tmp_path, 3459)

    assert patched.get(_PATH) is None
    patched.close()


def test_missing_entries_return_none(tmp_path: Path) -> None:
    cache = ThumbnailCache(tmp_path, 3458)

    assert cache.get(_PATH) is None
    cache.close()


def test_an_unusable_folder_disables_the_cache(tmp_path: Path) -> None:
    cache = ThumbnailCache(tmp_path / "missing", 3458)
    cache.put(_PATH, _URL)

    assert cache.error
    assert cache.get(_PATH) is None
