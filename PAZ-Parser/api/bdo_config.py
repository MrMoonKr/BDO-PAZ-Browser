"""User config in `paz_config.json` in the Data Folder: settings and per-file table sorts."""

from __future__ import annotations

import json
import logging
from collections.abc import Collection
from pathlib import Path

import app_dirs
from table_sort import TableSort

# Where the config lived before the Data Folder; `bdo_app.main()` moves it over.
LEGACY_CONFIG_FILE = Path(__file__).parent.parent / app_dirs.CONFIG_NAME

# {"buff.dbss": {"field": "duration_ms", "dir": "desc"}, ...}
_TABLE_SORT_KEY = "table_sort"


def config_file() -> Path:
    """`paz_config.json` in the Data Folder in use (`app_dirs.py`)."""
    return app_dirs.config_file()


def load_config() -> dict:
    path = config_file()
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}


def show_pa_tags_setting(cfg: dict) -> bool:
    """The "Show game text tags" setting; off unless saved as true."""
    return cfg.get("show_pa_tags") is True


def handled_only_setting(cfg: dict) -> bool:
    """The "Show only handled tables" setting; off unless saved as true."""
    return cfg.get("handled_only") is True


# "Parsed table cache": never, when a table is opened, or every table in the background.
RECORDS_CACHE_MODES = ("off", "open", "all")
_DEFAULT_RECORDS_CACHE_MODE = "open"


def records_cache_setting(cfg: dict) -> str:
    """The "Parsed table cache" mode; "open" unless a valid mode is saved."""
    mode = cfg.get("records_cache")
    return mode if mode in RECORDS_CACHE_MODES else _DEFAULT_RECORDS_CACHE_MODE


def dismissed_loc_warnings(cfg: dict) -> frozenset[str]:
    """Languages whose missing-LOC corner warning was dismissed for good."""
    codes = cfg.get("loc_warning_dismissed")
    return frozenset(code for code in codes if isinstance(code, str)) if isinstance(codes, list) else frozenset()


def save_config(updates: dict) -> None:
    cfg = {**load_config(), **updates}
    path = config_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cfg, indent=2))
    except OSError:
        logging.warning("Could not save the settings to %s", path, exc_info=True)


def table_sort_file_key(internal_path: str) -> str:
    """Config key for a file's sort: its lowercased file name.

    Handlers are chosen by file name, so every file sharing a name shares its
    columns and can share a sort.
    """
    return internal_path.replace("\\", "/").rsplit("/", 1)[-1].lower()


def _saved_table_sorts() -> dict:
    sorts = load_config().get(_TABLE_SORT_KEY)
    return sorts if isinstance(sorts, dict) else {}


def load_table_sort(file_key: str, sortable_fields: Collection[str]) -> TableSort | None:
    """The saved sort for a file, if its field is still sortable.

    A malformed entry, or one whose field the handler no longer declares, is
    dropped from the config so the file opens in its default sort from then on.
    """
    if file_key not in _saved_table_sorts():
        return None

    sort = peek_table_sort(file_key, sortable_fields)
    if sort is None:
        forget_table_sort(file_key)
    return sort


def peek_table_sort(file_key: str, sortable_fields: Collection[str]) -> TableSort | None:
    """`load_table_sort()` without dropping a stale entry, so it never writes the config."""
    saved = _saved_table_sorts().get(file_key)
    sort = TableSort.parse(saved.get("field"), saved.get("dir")) if isinstance(saved, dict) else None
    return sort if sort is not None and sort.field in sortable_fields else None


def save_table_sort(file_key: str, sort: TableSort) -> None:
    """Remember a file's sort. Writes only when it changed."""
    sorts = _saved_table_sorts()
    if sorts.get(file_key) == sort.to_dict():
        return
    save_config({_TABLE_SORT_KEY: {**sorts, file_key: sort.to_dict()}})


def forget_table_sort(file_key: str) -> None:
    sorts = _saved_table_sorts()
    if file_key not in sorts:
        return
    save_config({_TABLE_SORT_KEY: {key: value for key, value in sorts.items() if key != file_key}})
