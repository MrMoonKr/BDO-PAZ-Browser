"""Which handlers keep their parsed tables in memory, and when every handler drops them."""
from __future__ import annotations

from pathlib import Path

import pytest

import api.bdo_api_caches as caches
import api.bdo_config as bdo_config
import bdo_preview
from api.bdo_api import Api
from api.bdo_recent_tables import RecentTables
from bdo_models import PazEntry
from bdo_preview import PreviewHandler

_PATH = "gamecommondata/binary/numbers.dbss"


class _Handler(PreviewHandler):
    def __init__(self) -> None:
        self.builds = 0

    def get_records(self, data: bytes, entry: PazEntry, companions: dict[str, bytes]) -> list[dict]:
        self.builds += 1
        return [{"v": b} for b in data]

    def render_records_page(self, records: list[dict], page: int, page_size: int) -> str:
        return ""


def _entry(data: bytes) -> PazEntry:
    return PazEntry("test.paz", _PATH, 0, len(data), len(data), 0, 0)


def _parsed(handler: PreviewHandler, data: bytes) -> list[dict]:
    return handler.all_records(data, _entry(data), {})


def _keeps(handler: _Handler, data: bytes) -> bool:
    """True when `handler` still holds the records it parsed from `data`."""
    builds = handler.builds
    _parsed(handler, data)
    return handler.builds == builds


@pytest.fixture
def config_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "paz_config.json"
    monkeypatch.setattr(bdo_config, "CONFIG_FILE", path)
    return path


# ── RecentTables ─────────────────────────────────────────────────────────────

def test_the_oldest_handler_drops_its_tables() -> None:
    recent = RecentTables(keep=2)
    first, second, third = _Handler(), _Handler(), _Handler()
    for handler in (first, second, third):
        recent.viewed(handler)
        _parsed(handler, b"\x01\x02")

    recent.viewed(third)

    assert not _keeps(first, b"\x01\x02")
    assert _keeps(second, b"\x01\x02")
    assert _keeps(third, b"\x01\x02")


def test_viewing_a_kept_handler_again_keeps_it() -> None:
    recent = RecentTables(keep=2)
    first, second, third = _Handler(), _Handler(), _Handler()
    for handler in (first, second):
        recent.viewed(handler)
        _parsed(handler, b"\x01")

    recent.viewed(first)
    recent.viewed(third)

    assert _keeps(first, b"\x01")
    assert not _keeps(second, b"\x01")


def test_clear_drops_every_registered_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    never_viewed = _Handler()
    monkeypatch.setitem(bdo_preview._REGISTRY, "numbers.dbss", never_viewed)
    _parsed(never_viewed, b"\x01")

    RecentTables().clear()

    assert not _keeps(never_viewed, b"\x01")


# ── Api ──────────────────────────────────────────────────────────────────────

def test_opening_a_table_drops_the_one_before_it(config_file: Path) -> None:
    api = Api()
    api._recent_tables = RecentTables(keep=1)
    old, new = _Handler(), _Handler()
    old_data, new_data = b"\x01\x02", b"\x03"

    api._build_entry_response(old_data, _PATH, _entry(old_data), old, {}, {})
    api._build_entry_response(new_data, _PATH, _entry(new_data), new, {}, {})

    assert not _keeps(old, old_data)
    assert _keeps(new, new_data)


def test_new_loc_text_drops_every_table(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = _Handler()
    monkeypatch.setitem(bdo_preview._REGISTRY, "numbers.dbss", handler)
    monkeypatch.setattr(caches, "init_loc", lambda raw: None)
    api = Api()
    api._install_loc(b"english")
    _parsed(handler, b"\x01")

    api._install_loc(b"german")

    assert not _keeps(handler, b"\x01")


def test_the_same_loc_text_keeps_the_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = _Handler()
    monkeypatch.setitem(bdo_preview._REGISTRY, "numbers.dbss", handler)
    monkeypatch.setattr(caches, "init_loc", lambda raw: None)
    api = Api()
    api._install_loc(b"english")
    _parsed(handler, b"\x01")

    api._install_loc(b"english")

    assert _keeps(handler, b"\x01")
