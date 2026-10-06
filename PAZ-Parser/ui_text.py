"""UI text the Python side shows, from the same `ui/lang/*.json` files as the page.

Error messages, the status line, the preview's error boxes and tab labels and
the Save dialog filters are built in Python. They read their text here, so a
language file covers the whole UI. `ui_text()` works like `t()` in
`ui/js/core/i18n.js`: the active language first, then English, then the key
itself, with `{name}` placeholders filled from the arguments.
"""

from __future__ import annotations

import json
import logging
import re
from functools import cache
from pathlib import Path

_LANG_DIR = Path(__file__).parent / "ui" / "lang"
_FALLBACK = "en"
_PLACEHOLDER = re.compile(r"\{(\w+)\}")

_language = _FALLBACK


def set_ui_language(language: str) -> None:
    global _language
    _language = language


def ui_text(key: str, **args: object) -> str:
    """The text of `key` (`section.name`) in the active language."""
    path = key.split(".")
    text = _resolve(_strings(_language), path)
    if text is None:
        text = _resolve(_strings(_FALLBACK), path)
    if text is None:
        return key
    return fill_placeholders(text, **args)


def fill_placeholders(text: str, **args: object) -> str:
    """`text` with each `{name}` replaced by its argument; unknown names stay as they are."""
    return _PLACEHOLDER.sub(lambda match: str(args.get(match.group(1), match.group(0))), text)


@cache
def _strings(language: str) -> dict:
    path = _LANG_DIR / f"{language}.json"
    try:
        strings = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logging.warning("Could not read UI language file %s", path, exc_info=True)
        return {}
    return strings if isinstance(strings, dict) else {}


def _resolve(strings: dict, path: list[str]) -> str | None:
    node: object = strings
    for part in path:
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node if isinstance(node, str) else None
