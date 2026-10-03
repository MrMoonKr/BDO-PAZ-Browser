"""English production group names, built from the worldmap nodes.

The Korean label reads "node - work type" and has no LOC entry. Its two halves
come from the worldmap:

    production_key -> plantzone.dbss zone (record_id, a sub-node)
                   -> LOC type 29 sub-node name        "Lumbering"
    zone -> its one link in mapdata_realexplore2.bwp, the parent node
                   -> LOC type 29 parent node name     "Platerra Mountains"

A key gets a name only when every zone that uses it gives the same one, so a
key shared by zones under different nodes keeps its Korean label. The halves
follow the English worldmap names, which do not always match the Korean label
word for word.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping

from _common.node import node_name as loc_node_name


def english_group_names(
    zones: Iterable[dict],
    links: Mapping[int, frozenset[int]],
    node_name: Callable[[int], str] = loc_node_name,
) -> dict[int, str]:
    """Map each production key to its "parent node - sub-node" name, where unique.

    `zones` are `plantzone.dbss` records; `links` maps a waypoint key to the
    keys it links to (`neighbours()` of the worldmap waypoint graph).
    """
    labels: dict[int, set[str]] = {}
    for zone in zones:
        label = _zone_label(zone["record_id"], links, node_name)
        labels.setdefault(zone["production_key"], set()).add(label)

    return {
        key: next(iter(names))
        for key, names in labels.items()
        if len(names) == 1 and "" not in names
    }


def _zone_label(
    zone_key: int,
    links: Mapping[int, frozenset[int]],
    node_name: Callable[[int], str],
) -> str:
    """The "parent - sub" name of one zone, or '' without a single parent or a name."""
    linked = links.get(zone_key, frozenset())
    if len(linked) != 1:
        return ""

    (parent_key,) = linked
    parent_name, sub_name = node_name(parent_key), node_name(zone_key)
    return f"{parent_name} - {sub_name}" if parent_name and sub_name else ""
