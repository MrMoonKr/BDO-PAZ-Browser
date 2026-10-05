from __future__ import annotations

import gc
import threading
from collections.abc import Iterator

import pytest

from bdo_models import PazEntry
from bdo_preview import PreviewHandler
from gc_pause import gc_paused


@pytest.fixture(autouse=True)
def _collector_on() -> Iterator[None]:
    was_enabled = gc.isenabled()
    gc.enable()
    yield
    if not was_enabled:
        gc.disable()


def test_pause_turns_the_collector_off_and_back_on() -> None:
    with gc_paused():
        assert not gc.isenabled()

    assert gc.isenabled()


def test_nested_pause_resumes_only_after_the_outer_block() -> None:
    with gc_paused():
        with gc_paused():
            pass
        assert not gc.isenabled()

    assert gc.isenabled()


def test_pause_keeps_a_collector_that_was_already_off_off() -> None:
    gc.disable()

    with gc_paused():
        pass

    assert not gc.isenabled()


def test_pause_resumes_after_an_error() -> None:
    with pytest.raises(RuntimeError):
        with gc_paused():
            raise RuntimeError("boom")

    assert gc.isenabled()


def test_pause_on_another_thread_holds_until_both_end() -> None:
    entered = threading.Event()
    release = threading.Event()

    def other() -> None:
        with gc_paused():
            entered.set()
            release.wait()

    worker = threading.Thread(target=other)
    worker.start()
    entered.wait()
    with gc_paused():
        pass
    still_paused = not gc.isenabled()
    release.set()
    worker.join()

    assert still_paused
    assert gc.isenabled()


class _Handler(PreviewHandler):
    def get_records(self, data: bytes, entry: PazEntry, companions: dict[str, bytes]) -> list[dict]:
        return [{"collector_on": gc.isenabled()}]

    def render_records_page(self, records: list[dict], page: int, page_size: int) -> str:
        return ""


def test_cached_records_are_built_with_the_collector_paused() -> None:
    entry = PazEntry("test.paz", "foo.dbss", 0, 7, 7, 0, 0)

    records = _Handler().all_records(b"payload", entry, {})

    assert records == [{"collector_on": False}]
    assert gc.isenabled()
