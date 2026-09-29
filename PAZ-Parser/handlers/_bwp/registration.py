from __future__ import annotations

from bdo_preview import register_handler

from .waypoint.handler import WaypointBwpHandler


def register_bwp_handlers() -> None:
    # Every PABR .bwp file shares one layout.
    register_handler(".bwp", WaypointBwpHandler())
