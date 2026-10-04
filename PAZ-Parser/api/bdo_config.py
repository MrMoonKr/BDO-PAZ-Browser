"""User config in `paz_config.json`: settings and per-file table sorts."""

from __future__ import annotations

import json
from pathlib import Path

from table_sort import TableSort

CONFIG_FILE = Path(__file__).parent.parent / "paz_config.json"

# {"buff.dbss": {"field": "duration_ms", "dir": "desc"}, ...}
_TABLE_SORT_KEY = "table_sort"


def load_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
    except Exception:
        return {}


def show_pa_tags_setting(cfg: dict) -> bool:
    """The "Show game text tags" setting; off unless saved as true."""
    return cfg.get("show_pa_tags") is True


def handled_only_setting(cfg: dict) -> bool:
    """The "Show only handled tables" setting; off unless saved as true."""
    return cfg.get("handled_only") is True


def save_config(updates: dict) -> None:
    cfg = {**load_config(), **updates}
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    except Exception:
        pass


def table_sort_file_key(internal_path: str) -> str:
    """Config key for a file's sort: its lowercased file name.

    Handlers are chosen by file name, so every file sharing a name shares its
    columns and can share a sort.
    """
    return internal_path.replace("\\", "/").rsplit("/", 1)[-1].lower()


def _saved_table_sorts() -> dict:
    sorts = load_config().get(_TABLE_SORT_KEY)
    return sorts if isinstance(sorts, dict) else {}


def load_table_sort(file_key: str, sortable_fields: frozenset[str]) -> TableSort | None:
    """The saved sort for a file, if its field is still sortable.

    A malformed entry, or one whose field the handler no longer declares, is
    dropped from the config so the file opens unsorted from then on.
    """
    saved = _saved_table_sorts().get(file_key)
    if saved is None:
        return None

    sort = TableSort.parse(saved.get("field"), saved.get("dir")) if isinstance(saved, dict) else None
    if sort is None or sort.field not in sortable_fields:
        forget_table_sort(file_key)
        return None
    return sort


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
