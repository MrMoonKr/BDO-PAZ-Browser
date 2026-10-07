"""Versions of `paz_config.json` and the steps between them.

A breaking settings change (a renamed key, a new meaning for a value) appends
one step to `MIGRATIONS`: `MIGRATIONS[n - 1]` turns a version `n` config into
version `n + 1`, so the current version is always `len(MIGRATIONS) + 1`. A step
gets its own copy of the config, returns the new one, and raises `ValueError`
when it can't make sense of the old one. A new key with a default needs no step:
its reader falls back to the default when the key is missing.

A config without `config_version` is version 1, which covers everything written
before versions existed. A config from a newer app (after a downgrade) is
never migrated down: it is read as is, and its keys and version are kept on save.
"""

from __future__ import annotations

from collections.abc import Callable

VERSION_KEY = "config_version"

Migration = Callable[[dict], dict]

# MIGRATIONS[0] is 1 -> 2, MIGRATIONS[1] is 2 -> 3, and so on.
MIGRATIONS: tuple[Migration, ...] = ()


def current_version() -> int:
    """The config version this app writes."""
    return len(MIGRATIONS) + 1


def config_version(cfg: dict) -> int:
    """The version `cfg` was written with; 1 when it has none.

    Raises ValueError when the saved version is not a positive whole number.
    """
    version = cfg.get(VERSION_KEY, 1)
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise ValueError(f"{VERSION_KEY} is {version!r}, not a version number")
    return version


def needs_migration(cfg: dict) -> bool:
    return config_version(cfg) < current_version()


def migrate(cfg: dict) -> dict:
    """`cfg` brought to the current version, as a new dict; a current or newer one as is.

    Raises ValueError when the saved version is invalid or a step fails.
    """
    version = config_version(cfg)
    if version >= current_version():
        return cfg
    for step in MIGRATIONS[version - 1:]:
        cfg = step(dict(cfg))
        if not isinstance(cfg, dict):
            raise ValueError(f"{step.__name__} returned {type(cfg).__name__}, not a dict")
    return {**cfg, VERSION_KEY: current_version()}
