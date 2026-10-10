"""The world map outside the app: tile folders and single images (`browser.py --map-*`).

Both go through `world_map_build.build_map()`, so they show what the Map view
shows: hidden sectors and gaps drawn as sea.
"""

from __future__ import annotations

import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TypeVar

from world_map import SECTOR_CM, TILE_PX, Sector, WorldBounds
from world_map_build import MANIFEST_NAME, BuildProgress, MapManifest, build_map, tile_file

S = TypeVar("S")
TILES_FOLDER = "world_map_tiles"
IMAGE_QUALITY = 90


class ExportError(Exception):
    """An export that cannot run; the message says why."""


def image_name(zoom: int) -> str:
    return f"world_map_z{zoom}.jpg"


def image_size(bounds: WorldBounds, zoom: int) -> tuple[int, int]:
    """Width and height in pixels of the map at `zoom`."""
    scale = 2**zoom
    return (
        (bounds.max_x - bounds.min_x) // SECTOR_CM * scale,
        (bounds.max_z - bounds.min_z) // SECTOR_CM * scale,
    )


def export_tiles(
    *,
    sectors: Mapping[Sector, S],
    read: Callable[[S], bytes],
    folder: Path,
    version: int,
    workers: int,
    zoom: int | None,
    on_progress: Callable[[BuildProgress], None],
) -> tuple[Path, MapManifest]:
    """Write the tiles (every zoom, or only `zoom`) to `folder/world_map_tiles`.

    That folder is replaced when it holds an earlier export; any other folder
    of that name raises ExportError, so nothing that is not a map is deleted.
    """
    target = folder / TILES_FOLDER
    if target.exists() and not (target / MANIFEST_NAME).is_file():
        raise ExportError(f"{target} exists and is not a map export; move it or pick another --dir.")
    folder.mkdir(parents=True, exist_ok=True)
    manifest = build_map(
        sectors=sectors,
        read=read,
        target=target,
        version=version,
        workers=workers,
        zooms=None if zoom is None else (zoom,),
        on_progress=on_progress,
    )
    return target, manifest


def export_image(
    *,
    sectors: Mapping[Sector, S],
    read: Callable[[S], bytes],
    folder: Path,
    version: int,
    workers: int,
    zoom: int,
    on_progress: Callable[[BuildProgress], None],
) -> Path:
    """Write the whole map at `zoom` as one JPEG in `folder` and return its path.

    Builds the tiles down to `zoom` in a temporary folder, then stitches them.
    """
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="world_map_", dir=folder) as temp:
        tiles = Path(temp) / "tiles"
        manifest = build_map(
            sectors=sectors,
            read=read,
            target=tiles,
            version=version,
            workers=workers,
            zooms=(zoom,),
            on_progress=on_progress,
        )
        image = stitch(tiles, zoom, manifest.bounds)
        path = folder / image_name(zoom)
        image.save(path, format="JPEG", quality=IMAGE_QUALITY)
    return path


def stitch(folder: Path, zoom: int, bounds: WorldBounds):
    """The tiles of `zoom` in `folder`, cut to `bounds`, as one Pillow image (north up)."""
    from PIL import Image

    scale = 2**zoom / SECTOR_CM
    left, top = round(bounds.min_x * scale), round(-bounds.max_z * scale)
    width, height = image_size(bounds, zoom)
    canvas = Image.new("RGB", (width, height))
    for tile_y in range(top // TILE_PX, (top + height - 1) // TILE_PX + 1):
        for tile_x in range(left // TILE_PX, (left + width - 1) // TILE_PX + 1):
            path = tile_file(folder, zoom, (tile_x, tile_y))
            if path is None:
                continue
            with Image.open(path) as tile:
                canvas.paste(tile.convert("RGB"), (tile_x * TILE_PX - left, tile_y * TILE_PX - top))
    return canvas
