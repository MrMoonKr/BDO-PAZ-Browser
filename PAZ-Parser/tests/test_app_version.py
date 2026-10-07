"""The exe's version and commit, and the date versions releases use."""
from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

import app_version
from app_version import BuildInfo, build_info, parse_version


@pytest.fixture
def info_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    path = tmp_path / app_version.BUILD_INFO_NAME
    monkeypatch.setattr(app_version, "_BUILD_INFO_FILE", path)
    build_info.cache_clear()
    yield path
    build_info.cache_clear()


@pytest.mark.parametrize(
    ("text", "parsed"),
    [("2026.10.07", (2026, 10, 7)), ("v2026.10.07.2", (2026, 10, 7, 2))],
)
def test_date_versions_parse_to_numbers(text: str, parsed: tuple[int, ...]) -> None:
    assert parse_version(text) == parsed


def test_a_second_release_that_day_sorts_after_the_first() -> None:
    assert parse_version("2026.10.07.2") > parse_version("2026.10.07") > parse_version("2026.9.30")


@pytest.mark.parametrize("text", ["10.2026", "2026.10", "2026.10.07-beta", "", "2026.10.07.2.1"])
def test_anything_else_is_not_a_version(text: str) -> None:
    with pytest.raises(ValueError):
        parse_version(text)


def test_from_source_there_is_no_build(info_file: Path) -> None:
    assert build_info() is None


def test_the_exe_reads_its_version_and_commit(info_file: Path) -> None:
    info_file.write_text(json.dumps({"version": "2026.10.07", "commit": "08e271a"}), encoding="utf-8")

    assert build_info() == BuildInfo("2026.10.07", "08e271a")
    assert BuildInfo("2026.10.07", "08e271a").build_id == "2026.10.07+08e271a"


@pytest.mark.parametrize("content", ["{broken", json.dumps({"version": "2026.10.07"})], ids=["broken", "no-commit"])
def test_an_unreadable_build_file_reads_as_no_build(info_file: Path, content: str) -> None:
    info_file.write_text(content, encoding="utf-8")

    assert build_info() is None
