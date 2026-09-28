from __future__ import annotations

from pathlib import Path

import pytest

import tests.fixture_sync as fixture_sync
from tests.fixtures import FixtureFetchError
from tests.fixture_sync import ClientStamp, read_cached_stamp, sync_fixtures, write_cached_stamp

_OLD = ClientStamp(meta_version=1, meta_size=100, loc_size=10, loc_mtime_ns=5)
_NEW = ClientStamp(meta_version=2, meta_size=100, loc_size=10, loc_mtime_ns=5)


@pytest.fixture
def fixtures_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(fixture_sync, "FIXTURES_DIR", tmp_path)
    (tmp_path / "buff.dbss").write_bytes(b"")
    (tmp_path / ".gitkeep").write_bytes(b"")
    return tmp_path


@pytest.fixture
def fetched(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    calls: list[list[str]] = []
    monkeypatch.setattr(fixture_sync, "fetch_fixtures", calls.append)
    return calls


def _install(monkeypatch: pytest.MonkeyPatch, stamp: ClientStamp | None) -> None:
    monkeypatch.setattr(fixture_sync, "read_installed_stamp", lambda: stamp)


def test_stamp_round_trips(fixtures_dir: Path) -> None:
    write_cached_stamp(_OLD)

    assert read_cached_stamp() == _OLD


def test_stamp_of_another_shape_is_unknown(fixtures_dir: Path) -> None:
    (fixtures_dir / fixture_sync.STAMP_FILE_NAME).write_text('{"version": 1}', encoding="utf-8")

    assert read_cached_stamp() is None


def test_same_client_fetches_nothing(
    fixtures_dir: Path, fetched: list[list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    write_cached_stamp(_OLD)
    _install(monkeypatch, _OLD)

    sync_fixtures(force=False, report=lambda _: None)

    assert fetched == []


def test_changed_client_refetches_cached_files_and_restamps(
    fixtures_dir: Path, fetched: list[list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    write_cached_stamp(_OLD)
    _install(monkeypatch, _NEW)

    sync_fixtures(force=False, report=lambda _: None)

    assert fetched == [["buff.dbss"]]
    assert read_cached_stamp() == _NEW


def test_force_refetches_the_same_client(
    fixtures_dir: Path, fetched: list[list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    write_cached_stamp(_OLD)
    _install(monkeypatch, _OLD)

    sync_fixtures(force=True, report=lambda _: None)

    assert fetched == [["buff.dbss"]]


def test_no_client_keeps_the_cache(
    fixtures_dir: Path, fetched: list[list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    _install(monkeypatch, None)

    sync_fixtures(force=True, report=lambda _: None)

    assert fetched == []
    assert read_cached_stamp() is None


def test_failed_fetch_leaves_the_old_stamp(fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(_: list[str]) -> None:
        raise FixtureFetchError("boom")

    write_cached_stamp(_OLD)
    _install(monkeypatch, _NEW)
    monkeypatch.setattr(fixture_sync, "fetch_fixtures", fail)

    with pytest.raises(FixtureFetchError):
        sync_fixtures(force=False, report=lambda _: None)

    assert read_cached_stamp() == _OLD
