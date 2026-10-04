"""Worldmap node names, shared by the tables that link a node.

LOC type 29 names every `exploration.bss` node key. A sub-node holds only its
work there (`Mining`), so `full_node_name()` puts its parent node in front,
the way the worldmap and the node registration items name it: `Bambu Valley
- Mining`. The parent comes from the `NODE_PARENT` lookup index.
"""

from __future__ import annotations

from _common.loc import loc_text
from _common.lookup_index import IndexKind, lookup

LOC_NODE_NAME = 29


def node_name(node_key: int) -> str:
    """English name of a node as LOC stores it, or '' when LOC is not loaded or has none."""
    return loc_text(LOC_NODE_NAME, node_key)


def node_with_parent_name(node_key: int) -> str:
    """`Bambu Valley - Mining` for a sub-node with a known, named parent, else ''."""
    name = node_name(node_key)
    parent_key = lookup(IndexKind.NODE_PARENT, node_key)
    if not name or not isinstance(parent_key, int):
        return ""
    parent_name = node_name(parent_key)
    return f"{parent_name} - {name}" if parent_name else ""


def full_node_name(node_key: int) -> str:
    """`Bambu Valley - Mining` for a sub-node with a known parent, else `node_name()`."""
    return node_with_parent_name(node_key) or node_name(node_key)
