from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

import paz.source_fingerprint as fingerprint_module
from paz.bdo_index_cache import builder_fingerprint
from paz.source_fingerprint import project_modules, source_fingerprint


def test_fingerprint_covers_imported_helpers() -> None:
    from _dbss.itemenchant.parser import build_item_icon_index

    modules = project_modules([sys.modules[build_item_icon_index.__module__]])

    # find_prefixed_ascii decides which string is the icon, so it must count.
    assert "_common.prefixed_string" in modules
    assert "_common.binary" in modules
    # Standard library imports never do.
    assert not any(name.split(".")[0] == "re" for name in modules)


def test_fingerprint_covers_waypoint_helpers() -> None:
    from _dbss.teleport.parser import build_teleport_nearest_node_index

    modules = project_modules([sys.modules[build_teleport_nearest_node_index.__module__]])

    # The nearest node comes from the worldmap graph the _bwp parser reads.
    assert "_bwp.waypoint.parser" in modules


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
    monkeypatch.setattr(fingerprint_module, "_PROJECT_PACKAGES", frozenset({"fakepkg", "paz"}))

    builder = importlib.import_module("fakepkg.builder")

    yield builder.build, package

    for name in [name for name in sys.modules if name.split(".")[0] == "fakepkg"]:
        del sys.modules[name]


def test_fingerprint_is_stable_for_unchanged_code(fake_builder) -> None:
    build, _ = fake_builder

    assert builder_fingerprint([build]) == builder_fingerprint([build])


def test_editing_an_imported_helper_changes_the_fingerprint(fake_builder) -> None:
    build, package = fake_builder
    before = builder_fingerprint([build])

    (package / "helper.py").write_text("def scale(value):\n    return value.upper()\n")

    assert builder_fingerprint([build]) != before


def test_editing_a_lang_file_changes_the_fingerprint(fake_builder) -> None:
    build, package = fake_builder
    (package / "lang").mkdir()
    lang = package / "lang" / "en.json"
    lang.write_text('{"columns": {"name": "Name"}}')
    before = source_fingerprint([build])

    lang.write_text('{"columns": {"name": "Item"}}')

    assert source_fingerprint([build]) != before


def test_line_endings_do_not_change_the_fingerprint(fake_builder) -> None:
    build, package = fake_builder
    helper = package / "helper.py"
    source = b"def scale(value):\n    return value\n"

    helper.write_bytes(source)
    lf = builder_fingerprint([build])
    helper.write_bytes(source.replace(b"\n", b"\r\n"))

    assert builder_fingerprint([build]) == lf
