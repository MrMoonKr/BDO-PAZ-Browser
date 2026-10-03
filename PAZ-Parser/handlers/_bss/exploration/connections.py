"""A worldmap node's links, from `mapdata_realexplore2.bwp`.

The graph holds the links by node key; they are named the way the Node Name
column names the nodes, so a link reads the same as the row it points to.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from _common.node import node_name


def connection_fields(
    node_key: int,
    links: Mapping[int, frozenset[int]],
    node_names: Mapping[int, str],
    loc_name: Callable[[int], str] = node_name,
) -> dict:
    """The nodes `node_key` links to, by key and by name.

    `links` is `worldmap_links()`; `node_names` maps each `exploration.bss`
    node key to its Node Name. A few links go to waypoints the file has no
    record for: they take their LOC name, else the bare key.
    """
    keys = sorted(links.get(node_key, frozenset()))
    names = [node_names.get(key) or loc_name(key) or str(key) for key in keys]
    return {
        "connection_keys": keys,
        "connection_count": len(keys),
        "connection_names": names,
        # Full list as text, so tab search and CSV export see every name.
        "connection_text": ", ".join(names),
    }
