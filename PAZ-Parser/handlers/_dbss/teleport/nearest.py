"""The worldmap node nearest to a teleport point, to place a point without a name.

Distance is measured on the ground plane (x, z) in the shared world frame,
where one unit is a centimetre. Points inside instanced areas lie kilometres
from any node, which the distance shows.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from _bwp.waypoint.parser import Waypoint

_CENTIMETRES_PER_METRE = 100


@dataclass(frozen=True)
class NamedNode:
    key: int
    name: str
    x: float
    z: float


@dataclass(frozen=True)
class NearestNode:
    key: int
    name: str
    distance_m: float


def named_nodes(waypoints: Iterable[Waypoint], node_name: Callable[[int], str]) -> list[NamedNode]:
    """The nodes a point can be placed by: those with an English name.

    Without LOC no node has one, so every node takes its internal worldmap
    name (`town(velia)`) instead.
    """
    nodes = tuple(waypoints)
    named = [NamedNode(node.key, name, node.x, node.z) for node in nodes if (name := node_name(node.key))]
    if named:
        return named
    return [NamedNode(node.key, node.name, node.x, node.z) for node in nodes]


def nearest_node(x: float, z: float, nodes: Sequence[NamedNode]) -> NearestNode | None:
    """The node closest to (x, z), or None without nodes."""
    if not nodes:
        return None
    closest = min(nodes, key=lambda node: (node.x - x) ** 2 + (node.z - z) ** 2)
    distance = math.hypot(closest.x - x, closest.z - z) / _CENTIMETRES_PER_METRE
    return NearestNode(closest.key, closest.name, distance)
