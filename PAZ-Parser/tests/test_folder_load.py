"""The GUI folder load: the tree shows first, game text calls wait for LOC."""
from __future__ import annotations

import threading
from pathlib import Path

import pytest

from api.bdo_api import Api

_STATUS = {"key": "status.loadedFromCache", "args": {}}
# Long enough for a blocked call to return if it were not blocked; the check
# can only pass wrongly on a slow machine, never fail wrongly.
_BLOCKED_SECONDS = 0.2
_RETURN_SECONDS = 5.0


class _Recorder:
    def __init__(self, api: Api, monkeypatch: pytest.MonkeyPatch) -> None:
        self.steps: list[str] = []
        monkeypatch.setattr(api, "_push_js", lambda js: self.steps.append(js))
        monkeypatch.setattr(api, "_push_status", lambda msg, progress=None: self.steps.append(msg["key"]))
        monkeypatch.setattr(api, "_load_folder_entries", self._entries)

    def _entries(self, paz_root: Path, parse: object, *, read_loc: bool) -> tuple[dict, bytes | None]:
        self.steps.append("entries")
        return _STATUS, b"loc"


def _api(tmp_path: Path) -> Api:
    api = Api()
    api._paz_root = tmp_path
    return api


def test_the_tree_shows_before_the_game_text_loads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    api = _api(tmp_path)
    recorder = _Recorder(api, monkeypatch)
    ready_during_text: list[bool] = []

    def text(msg: dict, loc_raw: bytes | None, **_: bool) -> None:
        ready_during_text.append(api._folder_text_ready.is_set())
        recorder.steps.append("text")

    monkeypatch.setattr(api, "_load_folder_text", text)

    api._load_entries()

    assert recorder.steps == [
        "entries",
        "status.loadingText",
        "app.onFolderLoaded()",
        "text",
        "status.loadedFromCache",
    ]
    assert ready_during_text == [False]
    assert api._folder_text_ready.is_set()


def test_a_failed_text_load_releases_the_waiting_calls(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    api = _api(tmp_path)
    recorder = _Recorder(api, monkeypatch)

    def text(msg: dict, loc_raw: bytes | None, **_: bool) -> None:
        raise OSError("disk gone")

    monkeypatch.setattr(api, "_load_folder_text", text)

    api._load_entries()

    assert "status.error" in recorder.steps
    assert api._folder_text_ready.is_set()


def test_a_table_opened_during_the_text_load_waits_for_it(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    api = _api(tmp_path)
    _Recorder(api, monkeypatch)
    opened = threading.Event()
    opened_during_text: list[bool] = []

    def open_table() -> None:
        api.load_entry("gamecommondata/quest.dbss")
        opened.set()

    def text(msg: dict, loc_raw: bytes | None, **_: bool) -> None:
        threading.Thread(target=open_table, daemon=True).start()
        opened_during_text.append(opened.wait(_BLOCKED_SECONDS))

    monkeypatch.setattr(api, "_load_folder_text", text)

    api._load_entries()

    assert opened_during_text == [False]
    assert opened.wait(_RETURN_SECONDS)
