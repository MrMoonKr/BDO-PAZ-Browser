"""The world map's tile grid: radar sectors, the tile pyramid and world bounds.

The client's radar images are `minimap_data_pack/rader_X_Y.dds`, one 128 x 128
texture per world sector X, Y. A sector is 12,800 x 12,800 world units
(centimetres) on the X/Z ground plane, so 1 pixel is 100 cm and sector X, Y
spans world x X * 12800 to (X + 1) * 12800 and z Y * 12800 to (Y + 1) * 12800.
North is +z.

The map's tiles are 256 px. At `MAX_ZOOM` one tile holds 2 x 2 sectors, and
each lower zoom halves the scale. Tile indexes count from world (0, 0) with y
growing south, the scheme of Leaflet's `L.CRS.Simple` with a world CRS of
`1 / SECTOR_CM` (map-view.js), so world positions go on the map unconverted.
"""

from __future__ import annotations

import random
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import TypeVar

RADAR_FOLDER = "ui_texture/new_ui_common_forlua/widget/rader/minimap_data_pack"
_SECTOR_NAME = re.compile(rf"^{re.escape(RADAR_FOLDER)}/rader_(-?\d+)_(-?\d+)\.dds$", re.IGNORECASE)

SECTOR_CM = 12800
SECTOR_PX = 128
TILE_PX = 256
SECTORS_PER_TILE = TILE_PX // SECTOR_PX
MIN_ZOOM = 1
MAX_ZOOM = 7

# Sectors without a radar image get the radar image of one of these open sea
# sectors, picked per sector at random (all 12 are open sea on client 3464).
SEA_FILLER_SECTORS: tuple[tuple[int, int], ...] = tuple((x, 64) for x in range(-20, -8))
# Radar images with placeholder art or junk, drawn as sea instead: inclusive
# sector ranges (min x, min y, max x, max y), a hand-made cleanup list. Two
# ranges of that list that cover land with worldmap nodes (2104 and 2107 of
# mapdata_realexplore2.bwp, client 3464) are left out.
HIDDEN_SECTORS: tuple[tuple[int, int, int, int], ...] = (
    (-63, 75, 114, 91), (-134, 81, -125, 140), (-124, 125, -80, 140), (-80, 139, -74, 140),
    (-73, 140, -68, 140), (-62, 92, -24, 125), (-23, 92, 114, 140), (-73, -11, -54, 76),
    (-108, 56, -74, 70), (-134, -75, -74, 65), (-90, 71, -74, 74), (-73, -75, -56, -14),
    (-50, -75, -35, -53), (-34, -75, 24, -70), (-17, -55, -17, -55), (-22, -61, -22, -61),
    (-4, -59, -4, -59), (110, -75, 114, 66), (-55, -75, -51, -35), (-20, -59, -17, -58),
    (-20, -69, 2, -60), (3, -69, 16, -64), (77, -75, 109, -25), (69, -75, 76, -39),
    (66, -75, 70, -42), (65, -75, 65, -64), (60, -75, 64, -70), (59, -75, 65, -73),
    (3, -63, 4, -62), (8, -63, 9, -63), (10, -63, 14, -61), (55, -75, 59, -73),
    (103, -24, 109, -13), (98, -24, 103, -24), (101, -23, 102, -23), (102, -22, 102, -22),
    (-50, -52, -50, -47),
)
# A tile without any radar image under it, inside the map's bounds, shows one
# of this many sea tiles of its zoom (`sea_variant`), so the gaps cost a few files.
SEA_VARIANTS = 16
# Under everything else, and when a patch drops the filler sectors: the open
# sea colour, the most common tile mean of minimap_data_pack (10,971 of 27,691
# tiles on client 3464).
SEA_COLOR = (30, 54, 56)
# A JPEG tile on disk, averaged over a full build of client 3464
# (215,700,923 bytes over 9,802 tiles); the first-open prompt's size estimate.
AVERAGE_TILE_BYTES = 22_000

Sector = tuple[int, int]
TileKey = tuple[int, int]
S = TypeVar("S")


@dataclass(frozen=True)
class WorldBounds:
    """The world area the sectors cover, in world units."""

    min_x: int
    max_x: int
    min_z: int
    max_z: int

    def to_dict(self) -> dict[str, int]:
        return {"minX": self.min_x, "maxX": self.max_x, "minZ": self.min_z, "maxZ": self.max_z}


def find_sectors(paths: Iterable[str]) -> dict[Sector, str]:
    """Sector (X, Y) -> radar image path, for the radar images among `paths` (forward slashes)."""
    sectors: dict[Sector, str] = {}
    for path in paths:
        match = _SECTOR_NAME.match(path)
        if match:
            sectors[(int(match[1]), int(match[2]))] = path
    return sectors


def is_hidden(sector: Sector) -> bool:
    """True when `sector` is in `HIDDEN_SECTORS`."""
    x, y = sector
    return any(min_x <= x <= max_x and min_y <= y <= max_y for min_x, min_y, max_x, max_y in HIDDEN_SECTORS)


def visible_sectors(sectors: Mapping[Sector, S]) -> dict[Sector, S]:
    """`sectors` without the hidden ones; the build draws sea where those were."""
    return {sector: source for sector, source in sectors.items() if not is_hidden(sector)}


def native_tile(sector: Sector) -> TileKey:
    """The `MAX_ZOOM` tile that holds `sector`."""
    x, y = sector
    return x // SECTORS_PER_TILE, (-y - 1) // SECTORS_PER_TILE


def tile_sectors(tile: TileKey) -> tuple[Sector, Sector, Sector, Sector]:
    """The sectors of a `MAX_ZOOM` tile: top-left, top-right, bottom-left, bottom-right."""
    x, y = tile
    left, top = x * SECTORS_PER_TILE, -y * SECTORS_PER_TILE - 1
    return (left, top), (left + 1, top), (left, top - 1), (left + 1, top - 1)


def filler_sector(sector: Sector) -> Sector:
    """The `SEA_FILLER_SECTORS` sector drawn where `sector` has no radar image.

    Seeded with the sector, so every build picks the same one.
    """
    return random.Random(f"{sector[0]},{sector[1]}").choice(SEA_FILLER_SECTORS)


def sea_variant(zoom: int, tile: TileKey) -> int:
    """The sea tile shown for `tile` of `zoom` when it has no radar image under it."""
    return random.Random(f"{zoom},{tile[0]},{tile[1]}").randrange(SEA_VARIANTS)


def sea_parts(zoom: int, variant: int) -> tuple[int, int, int, int]:
    """What sea tile `variant` of `zoom` is made of, top-left to bottom-right.

    At `MAX_ZOOM`, indexes into `SEA_FILLER_SECTORS`; below it, sea variants
    of the zoom one in.
    """
    choices = len(SEA_FILLER_SECTORS) if zoom == MAX_ZOOM else SEA_VARIANTS
    pick = random.Random(f"sea {zoom},{variant}")
    return pick.randrange(choices), pick.randrange(choices), pick.randrange(choices), pick.randrange(choices)


def parent_tile(tile: TileKey) -> TileKey:
    """The tile one zoom out that holds `tile`."""
    return tile[0] // 2, tile[1] // 2


def child_tiles(tile: TileKey) -> tuple[TileKey, TileKey, TileKey, TileKey]:
    """The tiles one zoom in: top-left, top-right, bottom-left, bottom-right."""
    x, y = tile
    return (2 * x, 2 * y), (2 * x + 1, 2 * y), (2 * x, 2 * y + 1), (2 * x + 1, 2 * y + 1)


def pyramid(sectors: Iterable[Sector]) -> dict[int, frozenset[TileKey]]:
    """Zoom -> the tiles with at least one sector under them, `MAX_ZOOM` down to `MIN_ZOOM`."""
    level = frozenset(native_tile(sector) for sector in sectors)
    levels = {MAX_ZOOM: level}
    for zoom in range(MAX_ZOOM - 1, MIN_ZOOM - 1, -1):
        level = frozenset(parent_tile(tile) for tile in level)
        levels[zoom] = level
    return levels


def tile_count(levels: Mapping[int, frozenset[TileKey]]) -> int:
    """Files a build writes: the tiles of `levels` and the sea tiles of every zoom."""
    return sum(len(tiles) for tiles in levels.values()) + len(levels) * SEA_VARIANTS


def world_bounds(sectors: Iterable[Sector]) -> WorldBounds | None:
    """The world area of `sectors`, or None when there are none."""
    keys = list(sectors)
    if not keys:
        return None
    xs = [x for x, _ in keys]
    ys = [y for _, y in keys]
    return WorldBounds(
        min_x=min(xs) * SECTOR_CM,
        max_x=(max(xs) + 1) * SECTOR_CM,
        min_z=min(ys) * SECTOR_CM,
        max_z=(max(ys) + 1) * SECTOR_CM,
    )
