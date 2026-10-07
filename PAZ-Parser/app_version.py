"""Which build of the app is running: an exe's date version and commit, or the source.

`browser.spec` writes `build_info.json` next to this module in the exe at build
time; run from source there is none. Versions are dates, `2026.10.07`, with a
`.2` for a second release that day, so they sort as tuples of numbers.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from functools import cache
from pathlib import Path

BUILD_INFO_NAME = "build_info.json"
_BUILD_INFO_FILE = Path(__file__).parent / BUILD_INFO_NAME


@dataclass(frozen=True)
class BuildInfo:
    version: str
    commit: str

    @property
    def build_id(self) -> str:
        """Stands for the core modules, which an exe holds without their source."""
        return f"{self.version}+{self.commit}"


def is_frozen() -> bool:
    """True in the PyInstaller exe."""
    return bool(getattr(sys, "frozen", False))


@cache
def build_info() -> BuildInfo | None:
    """The exe's version and commit; None when running from source."""
    try:
        saved = json.loads(_BUILD_INFO_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        logging.warning("Could not read %s", _BUILD_INFO_FILE, exc_info=True)
        return None
    version, commit = saved.get("version"), saved.get("commit")
    if not isinstance(version, str) or not isinstance(commit, str):
        logging.warning("%s has no version and commit", _BUILD_INFO_FILE)
        return None
    return BuildInfo(version, commit)


def parse_version(text: str) -> tuple[int, ...]:
    """`2026.10.07.2` as (2026, 10, 7, 2). Raises ValueError for anything else."""
    parts = text.removeprefix("v").split(".")
    if len(parts) not in (3, 4) or not all(part.isdigit() for part in parts):
        raise ValueError(f"{text!r} is not a date version like 2026.10.07")
    return tuple(int(part) for part in parts)
