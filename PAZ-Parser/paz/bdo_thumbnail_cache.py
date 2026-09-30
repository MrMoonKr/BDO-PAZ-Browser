"""Disk cache for icon cell thumbnails, next to the PAZ entry cache.

A thumbnail of a large texture costs seconds: the 14 MB journal artwork of
`questjournalvideoinfo.bss` takes about 4.5 s just to decrypt and decompress.
Each finished thumbnail is stored here, so a texture is decoded once per client
version instead of once per session. The store is SQLite because thumbnails
arrive one at a time while the table scrolls; rewriting one pickle per icon, as
the index cache does for its single build, would not scale.

The meta version only changes with a game patch, so an open with another
version clears the store. A store that cannot be opened or written is disabled
for the session, logs a warning and keeps the reason in `error`; icons then
still load, just without the cache.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path

_CACHE_FILE = "paz_browser_thumbnails.sqlite"
_VERSION_KEY = "meta_version"

_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS thumbnails (path TEXT PRIMARY KEY, url TEXT NOT NULL)",
)


class ThumbnailCache:
    """Thumbnail data URLs by normalized icon path, for one client version."""

    def __init__(self, paz_root: Path, meta_version: int) -> None:
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None
        self.error = ""
        try:
            self._conn = self._open(paz_root / _CACHE_FILE, str(meta_version))
        except sqlite3.Error as ex:
            self._disable(ex)

    @staticmethod
    def _open(path: Path, version: str) -> sqlite3.Connection:
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            for statement in _SCHEMA:
                conn.execute(statement)
            row = conn.execute("SELECT value FROM meta WHERE key = ?", (_VERSION_KEY,)).fetchone()
            if row is None or row[0] != version:
                conn.execute("DELETE FROM thumbnails")
                conn.execute(
                    "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (_VERSION_KEY, version)
                )
            conn.commit()
        except sqlite3.Error:
            conn.close()
            raise
        return conn

    def _disable(self, ex: sqlite3.Error) -> None:
        self.error = f"{_CACHE_FILE}: {ex}"
        logging.warning("Thumbnail cache disabled: %s", self.error)
        if self._conn is not None:
            self._conn.close()
        self._conn = None

    def get(self, path: str) -> str | None:
        with self._lock:
            if self._conn is None:
                return None
            try:
                row = self._conn.execute("SELECT url FROM thumbnails WHERE path = ?", (path,)).fetchone()
            except sqlite3.Error as ex:
                self._disable(ex)
                return None
        return row[0] if row else None

    def put(self, path: str, url: str) -> None:
        with self._lock:
            if self._conn is None:
                return
            try:
                self._conn.execute(
                    "INSERT OR REPLACE INTO thumbnails (path, url) VALUES (?, ?)", (path, url)
                )
                self._conn.commit()
            except sqlite3.Error as ex:
                self._disable(ex)

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
