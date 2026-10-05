"""Disk cache for parsed table records and their sort orders, next to the PAZ entry cache.

Parsing a big table costs up to a second (`itemenchant.dbss`, `detail_dialog.dbss`)
while unpickling its records takes about a fifth of that. One row per table
path holds the records of its last parse, so the store never grows past one
copy of every table.

A records row is current when two things still match:

- `input_key`: the table's own bytes and handler code, computed by the caller
  (`api/bdo_records_store.py`).
- `deps`: the digest of every piece of shared data the build read, such as the
  LOC file or one lookup index, compared with today's digests.

A patch that leaves a table and the data it reads alone keeps its row.

Sorting a big table costs almost as much as unpickling it (0.38 s for
`itemenchant.dbss`), so sort orders are stored too, one row per table and sort.
An order row carries the `RecordsStamp` (input key and deps) of the records it
was computed from and is only served for records with that exact stamp, so an
order never indexes into other records. Saving new records drops the orders of
the old ones.

Like the thumbnail cache, a store that cannot be opened or written is disabled
for the session, logs a warning and keeps the reason in `error`.
"""

from __future__ import annotations

import json
import logging
import pickle
import sqlite3
import threading
from array import array
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

CACHE_FILE = "paz_browser_records.sqlite"

# Bump when the row layout or the pickled value changes shape; older stores
# are emptied on open.
_FORMAT = 2

_TABLES = ("records", "sort_orders")
_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS records ("
    "path TEXT PRIMARY KEY, input_key TEXT NOT NULL, deps TEXT NOT NULL, records BLOB NOT NULL)",
    "CREATE TABLE IF NOT EXISTS sort_orders ("
    "path TEXT NOT NULL, sort TEXT NOT NULL, input_key TEXT NOT NULL, deps TEXT NOT NULL, "
    "sort_order BLOB NOT NULL, PRIMARY KEY (path, sort))",
)

# Sort orders are record indices, as `bdo_preview.sorted_order()` keeps them.
_ORDER_TYPECODE = "I"

# Today's digest of one shared data dependency, by name.
CurrentDigest = Callable[[str], str]
T = TypeVar("T")


@dataclass(frozen=True)
class RecordsStamp:
    """Which build a set of records came from: its input key and read dependencies."""

    input_key: str
    deps: str

    @classmethod
    def of(cls, input_key: str, deps: Mapping[str, str]) -> RecordsStamp:
        return cls(input_key, json.dumps(dict(sorted(deps.items()))))

    def is_current(self, input_key: str, current: CurrentDigest) -> bool:
        if self.input_key != input_key:
            return False
        try:
            deps = json.loads(self.deps)
        except ValueError:
            return False
        return isinstance(deps, dict) and all(current(name) == digest for name, digest in deps.items())


@dataclass(frozen=True)
class CachedRecords:
    records: list[dict]
    stamp: RecordsStamp


class RecordsCache:
    """Pickled `get_records()` results and their sort orders, for one PAZ folder."""

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
            is_outdated = conn.execute("PRAGMA user_version").fetchone()[0] != _FORMAT
            if is_outdated:
                for table in _TABLES:
                    conn.execute(f"DROP TABLE IF EXISTS {table}")
                conn.execute(f"PRAGMA user_version = {_FORMAT}")
            for statement in _SCHEMA:
                conn.execute(statement)
            conn.commit()
            if is_outdated:
                # Dropping keeps the file at its old size; the settings show it.
                conn.execute("VACUUM")
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

    def _query(self, action: Callable[[sqlite3.Connection], T], default: T) -> T:
        """Run `action` under the lock; `default` when the store is disabled or fails."""
        with self._lock:
            if self._conn is None:
                return default
            try:
                return action(self._conn)
            except sqlite3.Error as ex:
                self._disable(ex)
                return default

    def _stamp(self, path: str) -> RecordsStamp | None:
        row = self._query(
            lambda conn: conn.execute("SELECT input_key, deps FROM records WHERE path = ?", (path,)).fetchone(),
            None,
        )
        return None if row is None else RecordsStamp(row[0], row[1])

    def get(self, path: str, input_key: str, current: CurrentDigest) -> CachedRecords | None:
        """The cached records of `path`, or None when absent or stale."""
        row = self._query(
            lambda conn: conn.execute(
                "SELECT input_key, deps, records FROM records WHERE path = ?", (path,)
            ).fetchone(),
            None,
        )
        if row is None:
            return None
        stamp = RecordsStamp(row[0], row[1])
        if not stamp.is_current(input_key, current):
            return None
        try:
            return CachedRecords(pickle.loads(row[2]), stamp)
        except Exception:
            logging.warning("Dropping unreadable cached records of %s", path, exc_info=True)
            self.forget(path)
            return None

    def is_current(self, path: str, input_key: str, current: CurrentDigest, sort: str | None = None) -> bool:
        """True when `get()` would hit, and `get_order(sort)` too when a sort is given."""
        stamp = self._stamp(path)
        if stamp is None or not stamp.is_current(input_key, current):
            return False
        return sort is None or self._has_order(path, sort, stamp)

    def put(self, path: str, stamp: RecordsStamp, records: list[dict]) -> None:
        """Store the records of `path`, replacing its previous row and that row's orders."""
        blob = pickle.dumps(records, protocol=pickle.HIGHEST_PROTOCOL)

        def write(conn: sqlite3.Connection) -> None:
            conn.execute(
                "INSERT OR REPLACE INTO records (path, input_key, deps, records) VALUES (?, ?, ?, ?)",
                (path, stamp.input_key, stamp.deps, blob),
            )
            conn.execute(
                "DELETE FROM sort_orders WHERE path = ? AND NOT (input_key = ? AND deps = ?)",
                (path, stamp.input_key, stamp.deps),
            )
            conn.commit()

        self._query(write, None)

    def get_order(self, path: str, sort: str, stamp: RecordsStamp) -> array | None:
        """The order `sort` gives the records stamped `stamp`, or None."""
        row = self._query(
            lambda conn: conn.execute(
                "SELECT sort_order FROM sort_orders WHERE path = ? AND sort = ? AND input_key = ? AND deps = ?",
                (path, sort, stamp.input_key, stamp.deps),
            ).fetchone(),
            None,
        )
        if row is None:
            return None
        order = array(_ORDER_TYPECODE)
        try:
            order.frombytes(row[0])
        except ValueError:
            return None
        return order

    def put_order(self, path: str, sort: str, stamp: RecordsStamp, order: array) -> None:
        def write(conn: sqlite3.Connection) -> None:
            conn.execute(
                "INSERT OR REPLACE INTO sort_orders (path, sort, input_key, deps, sort_order) "
                "VALUES (?, ?, ?, ?, ?)",
                (path, sort, stamp.input_key, stamp.deps, array(_ORDER_TYPECODE, order).tobytes()),
            )
            conn.commit()

        self._query(write, None)

    def _has_order(self, path: str, sort: str, stamp: RecordsStamp) -> bool:
        row = self._query(
            lambda conn: conn.execute(
                "SELECT 1 FROM sort_orders WHERE path = ? AND sort = ? AND input_key = ? AND deps = ?",
                (path, sort, stamp.input_key, stamp.deps),
            ).fetchone(),
            None,
        )
        return row is not None

    def forget(self, path: str) -> None:
        def delete(conn: sqlite3.Connection) -> None:
            conn.execute("DELETE FROM records WHERE path = ?", (path,))
            conn.execute("DELETE FROM sort_orders WHERE path = ?", (path,))
            conn.commit()

        self._query(delete, None)

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
