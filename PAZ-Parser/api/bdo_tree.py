"""The folder tree of PAZ entries, and the handled-files subset of it.

A tree is nested dicts keyed by path part, with a `PazEntry` at each file.
"""

from __future__ import annotations

from bdo_models import PazEntry
from bdo_preview import is_handled_file

from .bdo_api_helpers import _norm

TreeNode = dict | PazEntry


def build_tree(entries: list[PazEntry]) -> dict:
    root: dict = {}
    for entry in entries:
        parts = _norm(entry.internal_path).split("/")
        node = root
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = entry
    return root


def find_node(tree: dict, node_path: str) -> TreeNode | None:
    """The folder or file at `node_path`; the root for "", None when missing."""
    node: TreeNode = tree
    for part in node_path.split("/") if node_path else ():
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def collect_entries(node: TreeNode | None) -> list[PazEntry]:
    """Every entry at or below `node`."""
    if isinstance(node, PazEntry):
        return [node]
    if isinstance(node, dict):
        return [entry for child in node.values() for entry in collect_entries(child)]
    return []


def count_entries(node: dict) -> int:
    total = 0
    for child in node.values():
        if isinstance(child, PazEntry):
            total += 1
        elif isinstance(child, dict):
            total += count_entries(child)
    return total


def handled_entries(entries: list[PazEntry]) -> list[PazEntry]:
    """The entries a registered binary handler reads, in the given order.

    Companions a handler loads without being handled themselves are left out:
    handlers read them through the entry map, never through the tree.
    """
    return [
        entry
        for entry in entries
        if is_handled_file(_norm(entry.internal_path).rsplit("/", 1)[-1])
    ]
