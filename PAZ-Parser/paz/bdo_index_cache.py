"""Disk cache for the lookup indexes.

Building an index means decompressing its source table, 194 MB for
`itemenchant.dbss`, so the result is cached next to the PAZ entry cache and
invalidated on the same meta version. Mirrors `bdo_cache.py`. Values are pickled,
so an index may hold icon paths, linked IDs or tuples of IDs.

Indexes are stored keyed by `IndexKind.value` rather than by the enum member, so
renaming a kind cannot silently bind cached data to the wrong one.

The meta version only changes with a game patch, so a cache also records a
fingerprint of the code that built it (`builder_fingerprint`, see
`source_fingerprint.py`). Editing a builder, any project module it imports or
a JSON file beside one forces a rebuild on the next launch.
"""

from __future__ import annotations

import pickle
import sys
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path

from .source_fingerprint import source_fingerprint

_CACHE_FILE = "paz_browser_indexes.cache"
# Written before the icon indexes became general lookup indexes; removed on the
# first save so it does not linger next to the PAZ files.
_LEGACY_CACHE_FILE = "paz_browser_icons.cache"

# Values match `LookupValue` in handlers/_common/lookup_index.py.
CachedIndexes = dict[str, Mapping[int, int | str | tuple[int, ...]]]


def load_index_cache(
    paz_root: Path,
    fingerprint: str,
) -> tuple[int, CachedIndexes] | None:
    """Return (meta version, indexes), or None when absent, unreadable or stale."""
    cache_path = paz_root / _CACHE_FILE
    if not cache_path.exists():
        return None
    try:
        with cache_path.open("rb") as f:
            data = pickle.load(f)
        if data.get("fingerprint") != fingerprint:
            return None
        return data["version"], data["indexes"]
    except Exception:
        return None


def save_index_cache(
    paz_root: Path,
    version: int,
    fingerprint: str,
    indexes: CachedIndexes,
) -> None:
    cache_path = paz_root / _CACHE_FILE
    with cache_path.open("wb") as f:
        pickle.dump(
            {"fingerprint": fingerprint, "version": version, "indexes": indexes},
            f,
            protocol=pickle.HIGHEST_PROTOCOL,
        )
    (paz_root / _LEGACY_CACHE_FILE).unlink(missing_ok=True)


def builder_fingerprint(functions: Iterable[Callable]) -> str:
    """Hash the source of every project module that shapes the lookup indexes.

    Starts from the modules defining `functions` and always includes this
    module, so a change to the cache layout also counts.
    """
    return source_fingerprint([*functions, sys.modules[__name__]])
