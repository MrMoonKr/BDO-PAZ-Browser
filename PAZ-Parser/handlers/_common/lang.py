"""Handler-local string tables, with English filling every key a language leaves out."""

from __future__ import annotations

import json
import logging
from functools import cache
from pathlib import Path

_FALLBACK = "en"


def load_handler_strings(lang: str, strings_dir: str | Path) -> dict:
    """A handler's string table for *lang*, read from ``{strings_dir}/{lang}.json``.

    Every key the language file lacks comes from ``{strings_dir}/en.json``, at
    any depth, so a partial translation still shows a full table. Returns an
    empty dict when neither file exists. The table is read once per language
    and shared between calls, so treat it as read-only.

    Typical usage inside a handler package::

        from pathlib import Path
        from _common.lang import load_handler_strings

        _LANG_DIR = Path(__file__).parent / "lang"

        class MyHandler(PreviewHandler):
            def get_records(self, data, entry, companions):
                s = load_handler_strings(self.lang, _LANG_DIR)
                ...
    """
    return _merged_strings(lang, Path(strings_dir))


@cache
def _merged_strings(lang: str, strings_dir: Path) -> dict:
    english = _read_strings(strings_dir / f"{_FALLBACK}.json")
    if lang == _FALLBACK:
        return english
    return _merge(english, _read_strings(strings_dir / f"{lang}.json"))


def _read_strings(path: Path) -> dict:
    """The JSON object in `path`, or {} when it is missing or not a JSON object."""
    try:
        strings = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        logging.warning("Could not read handler string table %s", path, exc_info=True)
        return {}
    return strings if isinstance(strings, dict) else {}


def _merge(base: dict, override: dict) -> dict:
    """`base` with the values of `override` on top; nested sections merge key by key."""
    merged = dict(base)
    for key, value in override.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _merge(current, value)
        else:
            merged[key] = value
    return merged
