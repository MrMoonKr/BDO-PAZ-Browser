"""The "cache all tables" mode: parse every table without a current row, A to Z.

Parsing is pure Python, so a parse on this thread slows down whatever the UI
asks for at the same time. The fill therefore only starts a table while the app
is idle (`is_idle`), and finishes the one table it is on, at most about a
second, when the user comes back.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from bdo_models import PazEntry
from bdo_preview import PreviewHandler
from gc_pause import gc_paused
from table_sort import TableSort

from .bdo_records_store import RecordStore

# How often a paused fill checks whether the app is idle again.
_IDLE_POLL_S = 0.5
# How often the status line shows the latest progress.
_REPORT_INTERVAL_S = 0.25



@dataclass(frozen=True)
class PrefillProgress:
    """Where a pass is: `done` of `total` tables checked or parsed."""

    done: int
    total: int
    # The table being checked or parsed; empty while paused.
    path: str
    paused: bool = False


Target = tuple[PreviewHandler, PazEntry]
LoadTable = Callable[[PreviewHandler, PazEntry], tuple[bytes, dict[str, bytes]]]
# The sort a table opens with, whose order the fill caches with the records.
OpeningSort = Callable[[PreviewHandler, PazEntry], "TableSort | None"]


class RecordsPrefill:
    """One background pass over every table; `start()` again for a new pass."""

    def __init__(
        self,
        store: RecordStore,
        targets: Callable[[], Sequence[Target]],
        load: LoadTable,
        opening_sort: OpeningSort,
        is_idle: Callable[[], bool],
        report: Callable[[PrefillProgress], None],
        finished: Callable[[], None],
    ) -> None:
        self._store = store
        self._targets = targets
        self._load = load
        self._opening_sort = opening_sort
        self._is_idle = is_idle
        self._report = report
        self._finished = finished
        self._stop = threading.Event()
        # Set by the fill, read by the status ticker; replaced, never mutated.
        self._progress: PrefillProgress | None = None

    def start(self) -> None:
        """Stop a running pass and begin a new one from the first table."""
        self.stop()
        self._stop = threading.Event()
        threading.Thread(target=self._run, args=(self._stop,), name="records-prefill", daemon=True).start()

    def stop(self) -> None:
        """Ask the running pass to end; it does after its current table."""
        self._stop.set()

    def _run(self, stop: threading.Event) -> None:
        self._progress = None
        done = threading.Event()
        ticker = threading.Thread(target=self._tick, args=(done,), name="records-prefill-status", daemon=True)
        ticker.start()
        try:
            targets = sorted(self._targets(), key=lambda target: target[1].internal_path.lower())
            self._fill(targets, stop)
        except Exception:
            logging.warning("The background records cache fill stopped", exc_info=True)
        finally:
            done.set()
            ticker.join()
        # A stopped pass was replaced: a new pass or folder owns the status line.
        if not stop.is_set():
            self._finished()

    def _tick(self, done: threading.Event) -> None:
        """Report the latest progress while it changes, until the pass ends."""
        reported: PrefillProgress | None = None
        while not done.wait(_REPORT_INTERVAL_S):
            progress = self._progress
            if progress is not None and progress != reported:
                self._report(progress)
                reported = progress

    def _fill(self, targets: Sequence[Target], stop: threading.Event) -> None:
        total = len(targets)
        for index, (handler, entry) in enumerate(targets):
            if not self._wait_until_idle(stop, index, total):
                return
            self._progress = PrefillProgress(index, total, entry.internal_path)
            sort = self._opening_sort(handler, entry)
            if not self._store.is_current(handler, entry, sort):
                self._build(handler, entry, sort)

    def _build(self, handler: PreviewHandler, entry: PazEntry, sort: TableSort | None) -> None:
        """Parse one table into the cache, with its opening sort. A table that fails is logged and skipped."""
        try:
            data, companions = self._load(handler, entry)
        except Exception:
            logging.warning("Background fill could not read %s", entry.internal_path, exc_info=True)
            return
        try:
            with gc_paused():
                self._store.fill(handler, entry, lambda: handler.get_records(data, entry, companions), sort)
        except Exception:
            logging.warning("Background fill could not parse %s", entry.internal_path, exc_info=True)
        finally:
            # A handler that builds an index in get_records keeps it per payload.
            handler.release_data(data)

    def _wait_until_idle(self, stop: threading.Event, done: int, total: int) -> bool:
        """Block while the app is busy; False once the pass should stop."""
        while not stop.is_set() and not self._is_idle():
            self._progress = PrefillProgress(done, total, "", paused=True)
            stop.wait(_IDLE_POLL_S)
        return not stop.is_set()
