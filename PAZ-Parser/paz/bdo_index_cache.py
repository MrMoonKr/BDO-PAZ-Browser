"""Disk cache for the lookup indexes.

Building an index means decompressing its source table, 194 MB for
`itemenchant.dbss`, so the result is cached next to the PAZ entry cache and
invalidated on the same meta version. Mirrors `bdo_cache.py`. Values are pickled,
so an index may hold icon paths or linked IDs.

Indexes are stored keyed by `IndexKind.value` rather than by the enum member, so
renaming a kind cannot silently bind cached data to the wrong one.

The meta version only changes with a game patch, so a cache also records a
fingerprint of the code that built it (`builder_fingerprint`). Editing a
builder, or any project module it imports, changes the fingerprint and forces a
rebuild on the next launch, with no version number to remember to bump.
"""

from __future__ import annotations

import hashlib
import inspect
import pickle
import sys
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from types import ModuleType

_CACHE_FILE = "paz_browser_indexes.cache"
# Written before the icon indexes became general lookup indexes; removed on the
# first save so it does not linger next to the PAZ files.
_LEGACY_CACHE_FILE = "paz_browser_icons.cache"

CachedIndexes = dict[str, Mapping[int, int | str]]

# Top-level packages whose source can change what an index contains. Standard
# library and third-party imports are left out: they change with the
# interpreter, not with this project.
_PROJECT_PACKAGES = frozenset({"_common", "_dbss", "_bss", "paz"})


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

    Starts from the modules defining `functions`, follows their project imports
    transitively, and always includes this module, so a change to the cache
    layout also counts. Only file contents are hashed, with line endings
    normalised, never paths or times, so the value is stable across checkouts
    and machines.
    """
    modules = _project_modules(
        [sys.modules[fn.__module__] for fn in functions] + [sys.modules[__name__]]
    )
    digest = hashlib.sha256()
    for name in sorted(modules):
        digest.update(name.encode("utf-8"))
        source = Path(inspect.getfile(modules[name])).read_bytes()
        digest.update(source.replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def _project_modules(roots: list[ModuleType]) -> dict[str, ModuleType]:
    found: dict[str, ModuleType] = {}
    pending = list(roots)
    while pending:
        module = pending.pop()
        if module.__name__ in found:
            continue
        found[module.__name__] = module
        pending.extend(
            dep for dep in map(_defining_module, vars(module).values())
            if dep is not None and dep.__name__ not in found
        )
    return found


def _defining_module(value: object) -> ModuleType | None:
    """The project module a global came from, or None."""
    name = value.__name__ if inspect.ismodule(value) else getattr(value, "__module__", None)
    if not isinstance(name, str) or name.split(".")[0] not in _PROJECT_PACKAGES:
        return None
    module = sys.modules.get(name)
    return module if getattr(module, "__file__", None) else None
