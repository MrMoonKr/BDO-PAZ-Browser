from __future__ import annotations

import importlib
import pickle
import sys
from pathlib import Path

import pytest

import paz.bdo_index_cache as index_cache
from paz.bdo_index_cache import builder_fingerprint, load_index_cache, save_index_cache

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


def test_fingerprint_covers_imported_helpers() -> None:
    from _dbss.itemenchant.parser import build_item_icon_index

    modules = index_cache._project_modules([sys.modules[build_item_icon_index.__module__]])

    # find_prefixed_ascii decides which string is the icon, so it must count.
    assert "_common.prefixed_string" in modules
    assert "_common.binary" in modules
    # Standard library imports never do.
    assert not any(name.split(".")[0] == "re" for name in modules)


@pytest.fixture
def fake_builder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A throwaway `fakepkg` whose builder imports a helper module."""
    package = tmp_path / "fakepkg"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "helper.py").write_text("def scale(value):\n    return value\n")
    (package / "builder.py").write_text(
        "from fakepkg.helper import scale\n\n"
        "def build(data, offset_data):\n    return {1: scale('a.dds')}\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setattr(index_cache, "_PROJECT_PACKAGES", frozenset({"fakepkg", "paz"}))

    builder = importlib.import_module("fakepkg.builder")

    yield builder.build, package / "helper.py"

    for name in [name for name in sys.modules if name.split(".")[0] == "fakepkg"]:
        del sys.modules[name]


def test_fingerprint_is_stable_for_unchanged_code(fake_builder) -> None:
    build, _ = fake_builder

    assert builder_fingerprint([build]) == builder_fingerprint([build])


def test_editing_an_imported_helper_changes_the_fingerprint(fake_builder) -> None:
    build, helper = fake_builder
    before = builder_fingerprint([build])

    helper.write_text("def scale(value):\n    return value.upper()\n")

    assert builder_fingerprint([build]) != before


def test_line_endings_do_not_change_the_fingerprint(fake_builder) -> None:
    build, helper = fake_builder
    source = b"def scale(value):\n    return value\n"

    helper.write_bytes(source)
    lf = builder_fingerprint([build])
    helper.write_bytes(source.replace(b"\n", b"\r\n"))

    assert builder_fingerprint([build]) == lf
