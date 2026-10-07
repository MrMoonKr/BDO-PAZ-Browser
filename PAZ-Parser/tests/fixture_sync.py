"""Keep the cached fixtures on the same client version as the installed game.

A stamp file in the fixtures folder records which client the cached files came
from. At session start the stamp is compared with the installed client, and
every cached fixture is fetched again when they differ.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from paz.bdo_meta_reader import read_bdo_meta
from paz.bdo_paz_extract import find_single_meta_file

from .fixtures import FIXTURES_DIR, fetch_fixtures, find_external_fixture, installed_paz_folder


STAMP_FILE_NAME = ".client_stamp.json"
# Lives next to the PAZ folder rather than inside it, so the meta version does
# not cover it; its size and modified time stand in for a version.
LOC_FIXTURE_NAME = "languagedata_en.loc"


@dataclass(frozen=True)
class ClientStamp:
    meta_version: int
    meta_size: int
    loc_size: int | None
    loc_mtime_ns: int | None

    def describe(self) -> str:
        return f"client {self.meta_version}"


def sync_fixtures(force: bool, report: Callable[[str], None]) -> None:
    """Refresh every cached fixture when the installed client changed, or when forced.

    Raises `FixtureFetchError` when a fetch fails. The stamp is written only
    after every fetch succeeded, so a failed or partial refresh is retried on
    the next run.
    """
    installed = read_installed_stamp()
    if installed is None:
        report("fixtures: no installed client found, using cached fixtures as they are")
        return

    cached = read_cached_stamp()
    if cached == installed and not force:
        report(f"fixtures: up to date with {installed.describe()}")
        return

    names = cached_fixture_names()
    reason = "forced" if force else f"{_describe(cached)} -> {installed.describe()}"
    report(f"fixtures: refreshing {len(names)} files ({reason})")
    fetch_fixtures(names)
    write_cached_stamp(installed)


def read_installed_stamp() -> ClientStamp | None:
    paz_folder = installed_paz_folder()
    if paz_folder is None:
        return None

    try:
        meta_path = find_single_meta_file(paz_folder)
        meta_version = read_bdo_meta(meta_path).version
        meta_size = meta_path.stat().st_size
    except (OSError, ValueError):
        return None

    loc_path = find_external_fixture(LOC_FIXTURE_NAME)
    loc_stat = loc_path.stat() if loc_path is not None else None
    return ClientStamp(
        meta_version=meta_version,
        meta_size=meta_size,
        loc_size=loc_stat.st_size if loc_stat is not None else None,
        loc_mtime_ns=loc_stat.st_mtime_ns if loc_stat is not None else None,
    )


def read_cached_stamp() -> ClientStamp | None:
    try:
        return ClientStamp(**json.loads(_stamp_path().read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        # Missing, unreadable or from an older stamp shape: treat as unknown.
        return None


def write_cached_stamp(stamp: ClientStamp) -> None:
    _stamp_path().write_text(json.dumps(asdict(stamp), indent=2) + "\n", encoding="utf-8")


def cached_fixture_names() -> list[str]:
    if not FIXTURES_DIR.is_dir():
        return []
    return sorted(
        path.name
        for path in FIXTURES_DIR.iterdir()
        if path.is_file() and not path.name.startswith(".")
    )


def _stamp_path() -> Path:
    return FIXTURES_DIR / STAMP_FILE_NAME


def _describe(stamp: ClientStamp | None) -> str:
    return stamp.describe() if stamp is not None else "unknown client"
