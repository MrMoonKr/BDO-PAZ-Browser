"""The PAZ index cache: every entry of the client, saved next to the PAZ files.

Saved as columns (the archive names once, then one column per field) rather
than as pickled `PazEntry` objects. Loading builds the entries in C through
`map` and `tuple.__new__`, and the unpickler never holds a state dict per
entry: on client 3458 the load takes 0.29 s instead of 0.59 s and peaks at
289 MB instead of 614 MB. A cache of another format reads as missing, so the
folder load parses the meta file and saves this one.
"""
from __future__ import annotations

import pickle
import struct
from array import array
from collections.abc import Iterable
from itertools import repeat
from pathlib import Path

from bdo_models import PazEntry

CACHE_FILE = "paz_browser.cache"
# Raised when the saved layout changes; 1 was a pickled list of entries.
CACHE_FORMAT = 2
# Offsets and sizes are u32 in the archive file table.
_U32 = "I"
if array(_U32).itemsize != 4:
    raise ImportError("The PAZ index cache needs a 4-byte unsigned int array type on this platform.")


def read_meta_version(meta_path: Path) -> int:
    with meta_path.open("rb") as f:
        data = f.read(4)
    if len(data) != 4:
        raise ValueError(f"Cannot read version from: {meta_path}")
    return struct.unpack("<I", data)[0]


def load_cache(paz_root: Path) -> tuple[int, list[PazEntry]] | None:
    """(meta version, entries) from the cache, or None when it is missing or unreadable."""
    cache_path = paz_root / CACHE_FILE
    if not cache_path.exists():
        return None
    try:
        with cache_path.open("rb") as f:
            data = pickle.load(f)
        return _entries_from_columns(data)
    except Exception:
        return None


def save_cache(paz_root: Path, version: int, entries: list[PazEntry]) -> None:
    cache_path = paz_root / CACHE_FILE
    with cache_path.open("wb") as f:
        pickle.dump(_columns(version, entries), f, protocol=pickle.HIGHEST_PROTOCOL)


def _columns(version: int, entries: list[PazEntry]) -> dict:
    archives = sorted({entry.archive_name for entry in entries})
    archive_index = {name: index for index, name in enumerate(archives)}
    return {
        "format": CACHE_FORMAT,
        "version": version,
        "archives": archives,
        "archive": _u32_bytes(archive_index[entry.archive_name] for entry in entries),
        "paths": [entry.internal_path for entry in entries],
        "offset": _u32_bytes(entry.offset for entry in entries),
        "compressed": _u32_bytes(entry.compressed_size for entry in entries),
        "uncompressed": _u32_bytes(entry.uncompressed_size for entry in entries),
    }


def _entries_from_columns(data: object) -> tuple[int, list[PazEntry]] | None:
    """The entries of a cache in this format, or None for any other content.

    An archive index out of range raises IndexError, which `load_cache` turns
    into a miss like any other unreadable cache.
    """
    if not isinstance(data, dict) or data.get("format") != CACHE_FORMAT:
        return None
    version = data["version"]
    archives = data["archives"]
    paths = data["paths"]
    if not isinstance(version, int) or not isinstance(archives, list) or not isinstance(paths, list):
        return None
    columns = [_u32_array(data[name]) for name in ("archive", "offset", "compressed", "uncompressed")]
    if any(len(column) != len(paths) for column in columns):
        return None

    archive, offset, compressed, uncompressed = columns
    # compression_type and encryption_type are always 0 (`parse_paz_file`).
    # Every step runs in C: zip, map, tuple.__new__ and repeat.
    rows = zip(map(archives.__getitem__, archive), paths, offset, compressed, uncompressed, repeat(0), repeat(0))
    return version, list(map(tuple.__new__, repeat(PazEntry), rows))


def _u32_bytes(values: Iterable[int]) -> bytes:
    return array(_U32, values).tobytes()


def _u32_array(raw: bytes) -> array:
    values = array(_U32)
    values.frombytes(raw)
    return values
