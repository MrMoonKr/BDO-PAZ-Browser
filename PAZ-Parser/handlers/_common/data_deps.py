"""Which shared data a records build read: LOC, and which lookup indexes.

A table's records depend on its own bytes and handler code, and on the LOC and
lookup indexes the app injects (`loc.py`, `lookup_index.py`). LOC and the big
indexes change with nearly every patch, so the parsed records disk cache keys a
table only on the shared data its build actually read. `loc.py` and
`lookup_index.py` call `note_read()` on every access; `recording()` collects
those names while a build runs.

Recorders are shared across threads: a build on another thread at the same
time can add a name it did not read itself. That only makes a cache entry
stale sooner, never wrong.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager

LOC = "loc"
INDEX_PREFIX = "index:"

# Replaced, never mutated, so `note_read()` iterates a stable tuple while
# another thread starts or ends a recording.
_recorders: tuple[set[str], ...] = ()
_recorders_lock = threading.Lock()


def index_dep(kind_value: str) -> str:
    """Dependency name of one lookup index, by `IndexKind.value`."""
    return f"{INDEX_PREFIX}{kind_value}"


def note_read(dep: str) -> None:
    for deps in _recorders:
        deps.add(dep)


@contextmanager
def recording() -> Iterator[set[str]]:
    """Collect the dependency names read until the block ends."""
    global _recorders

    deps: set[str] = set()
    with _recorders_lock:
        _recorders = (*_recorders, deps)
    try:
        yield deps
    finally:
        with _recorders_lock:
            _recorders = tuple(other for other in _recorders if other is not deps)
