from __future__ import annotations

import fnmatch
from collections.abc import Callable

_DISK_VIRTUAL_PREFIX = "__disk__"

_ICON_MAP: dict[str, str] = {
    ".dds": "🖼", ".png": "🖼", ".jpg": "🖼", ".jpeg": "🖼", ".bmp": "🖼", ".tga": "🖼",
    ".xml": "📋", ".json": "📋", ".yaml": "📋", ".yml": "📋",
    ".txt": "📄", ".log": "📄", ".csv": "📄", ".ini": "📄", ".cfg": "📄",
    ".htm": "🌐", ".html": "🌐",
    ".lua": "📜",
    ".webm": "🎬",
    ".pac": "📦", ".bss": "🔒", ".dbss": "🔒",
    ".loc": "💬",
}


def _norm(path: str) -> str:
    return path.replace("\\", "/")


def _file_icon(ext: str) -> str:
    return _ICON_MAP.get(ext.lower(), "·")


def path_matcher(pattern: str) -> Callable[[str], bool]:
    """Test a normalised PAZ path against a search pattern, case-insensitively.

    A glob (containing *, ? or [) matches the full path or the file name
    alone; plain text matches anywhere in the path.
    """
    q = _norm(pattern).lower()
    if any(c in q for c in ("*", "?", "[")):
        def is_glob_hit(path: str) -> bool:
            path_lc = path.lower()
            name_lc = path_lc.rsplit("/", 1)[-1]
            return fnmatch.fnmatch(path_lc, q) or fnmatch.fnmatch(name_lc, q)
        return is_glob_hit

    return lambda path: q in path.lower()
