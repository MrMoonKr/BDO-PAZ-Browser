"""Disk cache for parsed table records, next to the PAZ entry cache.

Parsing a big table costs up to a second (`itemenchant.dbss`, `detail_dialog.dbss`)
while unpickling its records takes about a fifth of that. One row per table
path holds the records of its last parse, so the store never grows past one
copy of every table.

A row is current when two things still match:

- `input_key`: the table's own bytes and handler code, computed by the caller
  (`api/bdo_records_store.py`).
- `deps`: the digest of every piece of shared data the build read, such as the
  LOC file or one lookup index, compared with today's digests.

A patch that leaves a table and the data it reads alone keeps its row. Like the
thumbnail cache, a store that cannot be opened or written is disabled for the
session, logs a warning and keeps the reason in `error`.
"""

from __future__ import annotations

import json
import logging
import pickle
import sqlite3
import threading
from collections.abc import Callable, Mapping
from pathlib import Path

CACHE_FILE = "paz_browser_records.sqlite"

# Bump when the row layout or the pickled value changes shape; older stores
# are emptied on open.
_FORMAT = 1

_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS records ("
    "path TEXT PRIMARY KEY, input_key TEXT NOT NULL, deps TEXT NOT NULL, records BLOB NOT NULL)"
)

# Today's digest of one shared data dependency, by name.
CurrentDigest = Callable[[str], str]


class RecordsCache:
    """Pickled `get_records()` results by table path, for one PAZ folder."""

    def __init__(self, paz_root: Path) -> None:
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None
        self.error = ""
        try:
            self._conn = self._open(paz_root / CACHE_FILE)
        except sqlite3.Error as ex:
            self._disable(ex)

    @staticmethod
    def _open(path: Path) -> sqlite3.Connection:
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            if conn.execute("PRAGMA user_version").fetchone()[0] != _FORMAT:
                conn.execute("DROP TABLE IF EXISTS records")
                conn.execute(f"PRAGMA user_version = {_FORMAT}")
            conn.execute(_SCHEMA)
            conn.commit()
        except sqlite3.Error:
            conn.close()
            raise
        return conn

    def _disable(self, ex: Exception) -> None:
        self.error = f"{CACHE_FILE}: {ex}"
        logging.warning("Records cache disabled: %s", self.error)
        if self._conn is not None:
            self._conn.close()
        self._conn = None

    def get(self, path: str, input_key: str, current: CurrentDigest) -> list[dict] | None:
        """The cached records of `path`, or None when absent or stale."""
        with self._lock:
            if self._conn is None:
                return None
            try:
                row = self._conn.execute(
                    "SELECT input_key, deps, records FROM records WHERE path = ?", (path,)
                ).fetchone()
            except sqlite3.Error as ex:
                self._disable(ex)
                return None
        if row is None or not _is_current(row[0], row[1], input_key, current):
            return None
        try:
            return pickle.loads(row[2])
        except Exception:
            logging.warning("Dropping unreadable cached records of %s", path, exc_info=True)
            self.forget(path)
            return None

    def is_current(self, path: str, input_key: str, current: CurrentDigest) -> bool:
        """True when `get()` would hit, without reading the records."""
        with self._lock:
            if self._conn is None:
                return False
            try:
                row = self._conn.execute(
                    "SELECT input_key, deps FROM records WHERE path = ?", (path,)
                ).fetchone()
            except sqlite3.Error as ex:
                self._disable(ex)
                return False
        return row is not None and _is_current(row[0], row[1], input_key, current)

    def put(self, path: str, input_key: str, deps: Mapping[str, str], records: list[dict]) -> None:
        """Store the records of `path`, replacing its previous row."""
        blob = pickle.dumps(records, protocol=pickle.HIGHEST_PROTOCOL)
        with self._lock:
            if self._conn is None:
                return
            try:
                self._conn.execute(
                    "INSERT OR REPLACE INTO records (path, input_key, deps, records) VALUES (?, ?, ?, ?)",
                    (path, input_key, json.dumps(dict(sorted(deps.items()))), blob),
                )
                self._conn.commit()
            except sqlite3.Error as ex:
                self._disable(ex)

    def forget(self, path: str) -> None:
        with self._lock:
            if self._conn is None:
                return
            try:
                self._conn.execute("DELETE FROM records WHERE path = ?", (path,))
                self._conn.commit()
            except sqlite3.Error as ex:
                self._disable(ex)

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None


def _is_current(stored_key: str, stored_deps: str, input_key: str, current: CurrentDigest) -> bool:
    if stored_key != input_key:
        return False
    try:
        deps = json.loads(stored_deps)
    except ValueError:
        return False
    return isinstance(deps, dict) and all(current(name) == digest for name, digest in deps.items())
