"""Cached `entity ID -> value` lookups built from big source tables.

Some joins need a table far too large to open as a companion on every preview,
such as the 194 MB `itemenchant.dbss`. The app builds each lookup once per PAZ
folder, caches it on disk, and injects it here, the same way `loc.py` receives
LOC data. Handlers then read it by kind and ID and show a dash when the index is
not loaded.

`icon_index.py` layers overrides and ID derivation on top of the icon kinds.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum

# An icon path, one linked ID, or several linked IDs.
LookupValue = int | str | tuple[int, ...]


class IndexKind(Enum):
    """Every lookup index the app can build.

    Values double as disk-cache keys, so renaming one orphans its cached data
    until the next rebuild.
    """

    ITEM_ICON = "item_icon"
    QUEST_ICON = "quest_icon"
    CHARACTER_ICON = "character_icon"
    CHARACTER_ITEM = "character_item"
    KNOWLEDGE_CHARACTERS = "knowledge_characters"


# kind -> {entity_id: value}
_INDEXES: dict[IndexKind, Mapping[int, LookupValue]] = {}


def init_index(kind: IndexKind, mapping: Mapping[int, LookupValue] | None) -> None:
    """Install the index for one kind. Pass None to clear just that kind."""
    if mapping is None:
        _INDEXES.pop(kind, None)
        return

    _INDEXES[kind] = mapping


def clear_indexes() -> None:
    """Drop every loaded index, for a folder switch or a failed load."""
    _INDEXES.clear()


def is_index_loaded(kind: IndexKind) -> bool:
    return kind in _INDEXES


def index_size(kind: IndexKind) -> int:
    return len(_INDEXES.get(kind, ()))


def lookup(kind: IndexKind, entity_id: int) -> LookupValue | None:
    """The stored value, or None when the index is not loaded or lacks the ID."""
    return _INDEXES.get(kind, {}).get(entity_id)
