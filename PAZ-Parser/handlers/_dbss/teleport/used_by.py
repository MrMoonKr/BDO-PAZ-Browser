"""The buffs that teleport to a point, named the most readable way available.

A point has no name of its own. Each buff that goes there is named by the
item that applies it (`Footprints: Altinova's Wharf`), else its English text
(`Move to Altinova's Wharf`), else its Korean name, else its ID; the icon is
the item's, else the buff's, and an item name keeps its grade colour. Buffs
that read the same are listed once, with all their IDs in the hover text.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from _common.buff import buff_first_line
from _common.html import IconEntry, hidden_slice, icon_html_list_cell
from _common.icon_index import IconKind, icon_path
from _common.item_key import item_key_icon_path, item_key_text_tagged
from _common.lookup_index import IndexKind, lookup
from _common.pa_text import pa_html, strip_pa_tags
from _common.teleport import teleport_buff_name_kr


@dataclass(frozen=True)
class UsedBy:
    """One name in the Used By list and the buffs it stands for."""

    icon_path: str
    # The name with the item's grade colour tag, for `pa_fields`.
    tagged_label: str
    buff_ids: tuple[int, ...]

    @property
    def label(self) -> str:
        """The name as plain text."""
        return strip_pa_tags(self.tagged_label).strip()

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
    """(icon path, tagged label) of one buff that teleports to a point."""
    item_id = _first_item(buff_id)
    if item_id is not None:
        return item_key_icon_path(item_id), item_key_text_tagged(item_id)
    label = buff_first_line(buff_id) or teleport_buff_name_kr(buff_id) or str(buff_id)
    return icon_path(IconKind.BUFF, buff_id), label


def used_by_entries(buff_ids: Sequence[int]) -> list[UsedBy]:
    """One entry per distinct label, in buff ID order, holding every buff that reads so."""
    firsts: dict[str, IconEntry] = {}
    ids: dict[str, list[int]] = {}
    for buff_id in buff_ids:
        path, tagged_label = used_by_entry(buff_id)
        label = strip_pa_tags(tagged_label).strip()
        firsts.setdefault(label, (path, tagged_label))
        ids.setdefault(label, []).append(buff_id)
    return [UsedBy(*firsts[label], tuple(ids[label])) for label in firsts]


def used_by_cell(
    icon_paths: Sequence[str],
    tagged_labels: Sequence[str],
    tooltips: Sequence[str],
    max_items: int,
) -> str:
    """The first `max_items` entries with their icons, item grade colours and buff IDs on hover, and a count of the rest."""
    entries = [(path, pa_html(label)) for path, label in zip(icon_paths, tagged_labels)][:max_items]
    hidden = [strip_pa_tags(label).strip() for label in hidden_slice(tagged_labels, max_items)]
    return icon_html_list_cell(entries, len(tagged_labels) - len(entries), tooltips[:max_items], hidden)
