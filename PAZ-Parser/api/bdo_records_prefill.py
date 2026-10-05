"""The "cache all tables" mode: parse every table without a current row, A to Z.

Parsing is pure Python, so a parse on this thread slows down whatever the UI
asks for at the same time. The fill therefore only starts a table while the app
is idle (`is_idle`), and finishes the one table it is on, at most about a
second, when the user comes back.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Sequence

from bdo_models import PazEntry
from bdo_preview import PreviewHandler
from gc_pause import gc_paused

from .bdo_records_store import RecordStore

# How often a paused fill checks whether the app is idle again.
_IDLE_POLL_S = 0.5
# Least time between two progress reports.
_REPORT_INTERVAL_S = 0.5

Target = tuple[PreviewHandler, PazEntry]
LoadTable = Callable[[PreviewHandler, PazEntry], tuple[bytes, dict[str, bytes]]]


class RecordsPrefill:
    """One background pass over every table; `start()` again for a new pass."""

    def __init__(
        self,
        store: RecordStore,
        targets: Callable[[], Sequence[Target]],
        load: LoadTable,
        is_idle: Callable[[], bool],
        report: Callable[[int, int], None],
        finished: Callable[[int], None],
    ) -> None:
        self._store = store
        self._targets = targets
        self._load = load
        self._is_idle = is_idle
        self._report = report
        self._finished = finished
        self._stop = threading.Event()

    def start(self) -> None:
        """Stop a running pass and begin a new one from the first table."""
        self.stop()
        self._stop = threading.Event()
        threading.Thread(target=self._run, args=(self._stop,), name="records-prefill", daemon=True).start()

    def stop(self) -> None:
        """Ask the running pass to end; it does after its current table."""
        self._stop.set()

    def _run(self, stop: threading.Event) -> None:
        try:
            targets = sorted(self._targets(), key=lambda target: target[1].internal_path.lower())
            built = self._fill(targets, stop)
        except Exception:
            logging.warning("The background records cache fill stopped", exc_info=True)
            return
        if built and not stop.is_set():
            self._finished(built)

    def _fill(self, targets: Sequence[Target], stop: threading.Event) -> int:
        built = 0
        last_report = 0.0
        for done, (handler, entry) in enumerate(targets, start=1):
            if not self._wait_until_idle(stop):
                return built
            if self._store.is_current(handler, entry):
                continue
            self._build(handler, entry)
            built += 1
            now = time.monotonic()
            if now - last_report >= _REPORT_INTERVAL_S:
                self._report(done, len(targets))
                last_report = now
        return built

    def _build(self, handler: PreviewHandler, entry: PazEntry) -> None:
        """Parse one table into the cache. A table that fails is logged and skipped."""
        try:
            data, companions = self._load(handler, entry)
        except Exception:
            logging.warning("Background fill could not read %s", entry.internal_path, exc_info=True)
            return
        try:
            with gc_paused():
                self._store.build_and_save(handler, entry, lambda: handler.get_records(data, entry, companions))
        except Exception:
            logging.warning("Background fill could not parse %s", entry.internal_path, exc_info=True)
        finally:
            # A handler that builds an index in get_records keeps it per payload.
            handler.release_data(data)

    def _wait_until_idle(self, stop: threading.Event) -> bool:
        """Block while the app is busy; False once the pass should stop."""
        while not stop.is_set() and not self._is_idle():
            stop.wait(_IDLE_POLL_S)
        return not stop.is_set()
