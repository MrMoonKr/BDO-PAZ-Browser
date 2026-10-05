"""Which handlers keep their parsed tables in memory.

A handler's `_data_cache` slots keep the last payload it parsed, with its
records and sort views, until another payload replaces them. Every handler
holds its own, so a session that opens many big tables would keep all of
them: the 20 biggest take about 1 GB on client 3458. Only the handlers of
the last few tables viewed keep their slots; reopening an older table reads
the records cache again, or parses when the cache is off.
"""

from __future__ import annotations

import threading

from bdo_preview import PreviewHandler, clear_handler_caches

# Back and forth between a few tables stays instant; the worst case is about
# 0.7 GB (itemenchant.dbss, mapdata_realexplore.bwp, detail_dialog.dbss).
KEPT_TABLES = 3


class RecentTables:
    """The handlers of the last `keep` parsed tables viewed, newest first."""

    def __init__(self, keep: int = KEPT_TABLES) -> None:
        self._keep = keep
        self._handlers: tuple[PreviewHandler, ...] = ()
        self._lock = threading.Lock()

    def viewed(self, handler: PreviewHandler) -> None:
        """Mark `handler` viewed; a handler that falls out of the last `keep` drops its slots."""
        with self._lock:
            ordered = (handler, *(kept for kept in self._handlers if kept is not handler))
            self._handlers = ordered[: self._keep]
            dropped = ordered[self._keep :]
        for old in dropped:
            old.clear_data_cache()

    def clear(self) -> None:
        """Drop the slots of every parsed handler, after the data they were built from changed."""
        with self._lock:
            self._handlers = ()
        clear_handler_caches()
