"""Which lookup indexes exist and how each is built.

Every index is one `IndexSpec`: the tables it reads and the function that turns
them into `{entity_id: value}`. `build_indexes` reads each table once, so specs
that share a source reuse its payload, such as the 194 MB `itemenchant.dbss`
behind both the item icons and the character-to-item links.

Handlers are imported at module level so that `index_fingerprint()` reaches
every builder and helper that shapes the result.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast

from _common.icon_index import borrow_icons
from _bss.buffsimply.parser import build_buff_icon_index
from _common.lookup_index import IndexKind, LookupValue
from _dbss.characterobject.parser import build_character_icon_index
from _dbss.characterstatic.parser import build_knowledge_character_index
from _dbss.detail_dialog.parser import build_character_lease_index
from _dbss.itemenchant.parser import build_character_item_index, build_item_icon_index
from _dbss.quest.parser import build_quest_icon_index
from _dbss.skilltype.parser import build_skill_icon_index, build_skill_name_index
from paz.bdo_index_cache import CachedIndexes, builder_fingerprint

_BINARY = "gamecommondata/binary"
ITEMENCHANT = f"{_BINARY}/itemenchant.dbss"
ITEMENCHANT_OFFSET = f"{_BINARY}/itemenchantoffset.dbss"
QUEST = f"{_BINARY}/quest.dbss"
ALLQUESTLIST = f"{_BINARY}/allquestlist.bss"
CHARACTEROBJECT = f"{_BINARY}/characterobject.dbss"
CHARACTEROBJECT_OFFSET = f"{_BINARY}/characterobjectoffset.dbss"
CHARACTERSTATIC = f"{_BINARY}/characterstatic.dbss"
CHARACTERSTATIC_OFFSET = f"{_BINARY}/characterstaticoffset.dbss"
DETAIL_DIALOG = f"{_BINARY}/detail_dialog.dbss"
DETAIL_DIALOG_OFFSET = f"{_BINARY}/detail_dialogoffset.dbss"
SKILLTYPE = f"{_BINARY}/skilltype.dbss"
SKILLTYPE_OFFSET = f"{_BINARY}/skilltypeoffset.dbss"
BUFFSIMPLY = f"{_BINARY}/buffsimply.bss"


@dataclass(frozen=True)
class IndexSpec:
    """One index: `build` receives the payloads of `sources`, in that order."""

    kind: IndexKind
    sources: tuple[str, ...]
    build: Callable[..., Mapping[int, LookupValue]]


# Adding an index is one entry here plus its `IndexKind` member.
INDEX_SPECS: tuple[IndexSpec, ...] = (
    IndexSpec(IndexKind.ITEM_ICON, (ITEMENCHANT, ITEMENCHANT_OFFSET), build_item_icon_index),
    IndexSpec(IndexKind.QUEST_ICON, (QUEST, ALLQUESTLIST), build_quest_icon_index),
    IndexSpec(
        IndexKind.CHARACTER_ICON,
        (CHARACTEROBJECT, CHARACTEROBJECT_OFFSET),
        build_character_icon_index,
    ),
    IndexSpec(
        IndexKind.CHARACTER_ITEM,
        (ITEMENCHANT, ITEMENCHANT_OFFSET),
        build_character_item_index,
    ),
    IndexSpec(
        IndexKind.KNOWLEDGE_CHARACTERS,
        (CHARACTERSTATIC, CHARACTERSTATIC_OFFSET),
        build_knowledge_character_index,
    ),
    IndexSpec(
        IndexKind.CHARACTER_LEASES,
        (DETAIL_DIALOG, DETAIL_DIALOG_OFFSET),
        build_character_lease_index,
    ),
    IndexSpec(IndexKind.SKILL_ICON, (SKILLTYPE, SKILLTYPE_OFFSET), build_skill_icon_index),
    IndexSpec(IndexKind.SKILL_NAME_KR, (SKILLTYPE, SKILLTYPE_OFFSET), build_skill_name_index),
    # buffsimply.bss holds the buff.dbss icon paths in fixed rows, 1.4 MB against 12 MB.
    IndexSpec(IndexKind.BUFF_ICON, (BUFFSIMPLY,), build_buff_icon_index),
)


def index_fingerprint() -> str:
    """Hash of the code that decides what the indexes contain."""
    return builder_fingerprint([build_indexes])


def build_indexes(
    read: Callable[[str], bytes | None],
    exists: Callable[[str], bool],
    specs: tuple[IndexSpec, ...] = INDEX_SPECS,
) -> CachedIndexes:
    """Build every spec whose sources are all present, keyed by kind value.

    `read` returns a PAZ payload or None; `exists` answers whether a PAZ path
    is shipped, for the character icon borrowing step.
    """
    payloads: dict[str, bytes | None] = {}

    def load(path: str) -> bytes | None:
        if path not in payloads:
            payloads[path] = read(path)
        return payloads[path]

    indexes: CachedIndexes = {}
    for spec in specs:
        data = [load(path) for path in spec.sources]
        if any(payload is None for payload in data):
            continue
        indexes[spec.kind.value] = dict(spec.build(*data))

    return _with_borrowed_character_icons(indexes, exists)


def _with_borrowed_character_icons(
    indexes: CachedIndexes,
    exists: Callable[[str], bool],
) -> CachedIndexes:
    """Give characters without a working icon the icon of their item.

    Fences, crops and pets often store no icon, or one the client does not
    ship, while the item that places or summons them does.
    """
    characters = indexes.get(IndexKind.CHARACTER_ICON.value)
    items = indexes.get(IndexKind.ITEM_ICON.value)
    links = indexes.get(IndexKind.CHARACTER_ITEM.value)
    if characters is None or items is None or links is None:
        return indexes

    # The builders fix the value types: icon kinds hold paths, links hold IDs.
    merged = borrow_icons(
        cast(dict[int, str], characters),
        cast(dict[int, str], items),
        cast(dict[int, int], links),
        exists,
    )
    return {**indexes, IndexKind.CHARACTER_ICON.value: merged}
