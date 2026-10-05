"""Keep the garbage collector off while a big table is built."""
from __future__ import annotations

import gc
import threading
from collections.abc import Iterator
from contextlib import contextmanager

_lock = threading.Lock()
_depth = 0
_was_enabled = False


@contextmanager
def gc_paused() -> Iterator[None]:
    """Turn the collector off for the block, back to its old state after it.

    Parsing a big table allocates hundreds of thousands of dicts that all stay
    alive. Each burst sets off collections, and the full ones walk the loaded
    LOC and lookup indexes for nothing: measured 2026-10-05, `itemenchant.dbss`
    parsed 1.29x and `detail_dialog.dbss` 1.52x faster with it off. Parsed
    records hold no reference cycles, so nothing waits on the collector.

    The collector is process wide, so nested blocks and blocks on other
    threads share one pause, and the state from before the first block comes
    back when the last one ends.
    """
    global _depth, _was_enabled
    with _lock:
        if _depth == 0:
            _was_enabled = gc.isenabled()
            gc.disable()
        _depth += 1
    try:
        yield
    finally:
        with _lock:
            _depth -= 1
            if _depth == 0 and _was_enabled:
                gc.enable()
