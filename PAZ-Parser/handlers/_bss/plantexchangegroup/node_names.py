"""English production group names, built from the worldmap nodes.

The Korean label reads "node - work type" and has no LOC entry. Each zone that
uses a production key is an `exploration.bss` sub-node, so it has the same
name the worldmap gives it:

    production_key -> plantzone.dbss zone (record_id, a sub-node)
                   -> node_with_parent_name()   "Platerra Mountains - Lumbering"

A key gets a name only when every zone that uses it gives the same one, so a
key shared by zones under different nodes keeps its Korean label. The names
follow the English worldmap names, which do not always match the Korean label
word for word.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from _common.node import node_with_parent_name


def english_group_names(
    zones: Iterable[dict],
    zone_name: Callable[[int], str] = node_with_parent_name,
) -> dict[int, str]:
    """Map each production key to its "parent node - sub-node" name, where unique.

    `zones` are `plantzone.dbss` records; `zone_name` names a zone key, or
    returns '' when the zone has no parent or no name.
    """
    labels: dict[int, set[str]] = {}
    for zone in zones:
        labels.setdefault(zone["production_key"], set()).add(zone_name(zone["record_id"]))

    return {
        key: next(iter(names))
        for key, names in labels.items()
        if len(names) == 1 and "" not in names
    }
