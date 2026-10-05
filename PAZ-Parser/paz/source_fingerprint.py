"""Hash of the project code, and the data files next to it, that produced a cached value.

The disk caches outlive the code that filled them. A cache records this
fingerprint and treats a mismatch as stale, so editing a builder, a helper it
imports or a JSON file its package reads forces a rebuild, with no version
number to remember to bump.
"""

from __future__ import annotations

import hashlib
import inspect
import sys
from collections.abc import Iterable
from pathlib import Path
from types import ModuleType

# Top-level packages whose source can change what a cached value contains.
# Standard library and third-party imports are left out: they change with the
# interpreter, not with this project.
_PROJECT_PACKAGES = frozenset({"_common", "_dbss", "_bss", "_bwp", "paz"})

# Data files a package reads next to its modules: column labels and values in
# `lang/*.json`, overrides such as `_common/icon_overrides.json`.
_DATA_PATTERNS = ("*.json", "lang/*.json")


def source_fingerprint(roots: Iterable[object]) -> str:
    """Hash the source of every project module that `roots` reach.

    `roots` are modules, or functions and classes standing for the module that
    defines them; they count whatever package they live in. Their project
    imports are followed transitively. The JSON files beside each module count
    too. Only file contents are hashed, with line endings normalised, never
    paths or times, so the value is stable across checkouts and machines.
    """
    modules = project_modules([_module_of(root) for root in roots])
    digest = hashlib.sha256()
    for name in sorted(modules):
        digest.update(name.encode("utf-8"))
        digest.update(_normalised(Path(inspect.getfile(modules[name]))))
    for path in _data_files(modules.values()):
        digest.update(path.name.encode("utf-8"))
        digest.update(_normalised(path))
    return digest.hexdigest()


def project_modules(roots: list[ModuleType]) -> dict[str, ModuleType]:
    """`roots` plus every project module they import, directly or not, by name."""
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


def _module_of(root: object) -> ModuleType:
    return root if isinstance(root, ModuleType) else sys.modules[getattr(root, "__module__")]


def _defining_module(value: object) -> ModuleType | None:
    """The project module a global came from, or None."""
    name = value.__name__ if inspect.ismodule(value) else getattr(value, "__module__", None)
    if not isinstance(name, str) or name.split(".")[0] not in _PROJECT_PACKAGES:
        return None
    module = sys.modules.get(name)
    return module if getattr(module, "__file__", None) else None


def _data_files(modules: Iterable[ModuleType]) -> list[Path]:
    """The JSON files beside `modules`, once each, in a stable order."""
    folders = {Path(inspect.getfile(module)).parent for module in modules}
    found = {path for folder in folders for pattern in _DATA_PATTERNS for path in folder.glob(pattern)}
    return sorted(found, key=lambda path: path.as_posix())


def _normalised(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")
