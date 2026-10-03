"""The buffs that teleport to a point, named the most readable way available.

A point has no name of its own. Each buff that goes there is named by the
item that applies it (`Footprints: Altinova's Wharf`), else its English text
(`Move to Altinova's Wharf`), else its Korean name, else its ID; the icon is
the item's, else the buff's. Buffs that read the same are listed once, with
all their IDs in the hover text.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from _common.buff import buff_first_line
from _common.html import IconEntry, icon_list_cell
from _common.icon_index import IconKind, icon_path
from _common.item_key import item_key_icon_path, item_key_text
from _common.lookup_index import IndexKind, lookup
from _common.teleport import teleport_buff_name_kr


@dataclass(frozen=True)
class UsedBy:
    """One name in the Used By list and the buffs it stands for."""

    icon_path: str
    label: str
    buff_ids: tuple[int, ...]

    @property
    def tooltip(self) -> str:
        """`Buff 47341`, or `Buffs 54978, 54979` for several."""
        ids = ", ".join(str(buff_id) for buff_id in self.buff_ids)
        return f"Buff {ids}" if len(self.buff_ids) == 1 else f"Buffs {ids}"


def _first_item(buff_id: int) -> int | None:
    """The lowest base item whose skills apply the buff, from BUFF_ITEMS."""
    item_ids = lookup(IndexKind.BUFF_ITEMS, buff_id)
    return item_ids[0] if isinstance(item_ids, tuple) and item_ids else None


def used_by_entry(buff_id: int) -> IconEntry:
    """(icon path, label) of one buff that teleports to a point."""
    item_id = _first_item(buff_id)
    if item_id is not None:
        return item_key_icon_path(item_id), item_key_text(item_id)
    label = buff_first_line(buff_id) or teleport_buff_name_kr(buff_id) or str(buff_id)
    return icon_path(IconKind.BUFF, buff_id), label


def used_by_entries(buff_ids: Sequence[int]) -> list[UsedBy]:
    """One entry per distinct label, in buff ID order, holding every buff that reads so."""
    paths: dict[str, str] = {}
    ids: dict[str, list[int]] = {}
    for buff_id in buff_ids:
        path, label = used_by_entry(buff_id)
        paths.setdefault(label, path)
        ids.setdefault(label, []).append(buff_id)
    return [UsedBy(paths[label], label, tuple(ids[label])) for label in paths]


def used_by_cell(
    icon_paths: Sequence[str],
    labels: Sequence[str],
    tooltips: Sequence[str],
    max_items: int,
) -> str:
    """The first `max_items` entries with their icons and buff IDs on hover, and a count of the rest."""
    entries = list(zip(icon_paths, labels))[:max_items]
    return icon_list_cell(entries, len(labels) - len(entries), tooltips[:max_items])
