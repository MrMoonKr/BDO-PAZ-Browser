"""`browser.py --map-tiles` and `--map-image`: the Map view's world map as files."""

from __future__ import annotations

import argparse
from pathlib import Path

from api.bdo_api_helpers import _norm
from paz.bdo_cache import read_meta_version
from paz.bdo_paz_extract import find_single_meta_file
from world_map import MAX_ZOOM, Sector, find_sectors, visible_sectors
from world_map_build import BuildProgress, RadarSource, read_radar, worker_count
from world_map_export import ExportError, export_image, export_tiles

from .errors import CliError
from .session import open_session
from .stdio import error, progress

# --map-image without --zoom: 32 px per sector, 7968 x 6912 on client 3464.
DEFAULT_IMAGE_ZOOM = 5


def run_map_tiles(args: argparse.Namespace) -> int:
    try:
        sources, version = _radar_sources(args)
        folder, manifest = export_tiles(
            sectors=sources,
            read=read_radar,
            folder=Path(args.dir),
            version=version,
            workers=worker_count(),
            zoom=args.zoom,
            on_progress=_print_progress,
        )
    except (CliError, ExportError, ValueError) as ex:
        error(str(ex))
        return 1
    progress(f"Done: {manifest.tiles:,} tiles, {manifest.bytes / 1e6:,.1f} MB in {folder}")
    return 0


def run_map_image(args: argparse.Namespace) -> int:
    zoom = DEFAULT_IMAGE_ZOOM if args.zoom is None else args.zoom
    try:
        sources, version = _radar_sources(args)
        if zoom == MAX_ZOOM:
            progress("Zoom 7 is the radar images' full size; the image needs about 3 GB of memory.")
        path = export_image(
            sectors=sources,
            read=read_radar,
            folder=Path(args.dir),
            version=version,
            workers=worker_count(),
            zoom=zoom,
            on_progress=_print_progress,
        )
    except (CliError, ExportError, ValueError) as ex:
        error(str(ex))
        return 1
    progress(f"Done: {path}")
    return 0


def _radar_sources(args: argparse.Namespace) -> tuple[dict[Sector, RadarSource], int]:
    """The visible radar images of the PAZ folder and its client version."""
    api = open_session(args.paz_folder, load_loc=False, load_indexes=False)
    assert api.paz_root is not None  # set by open_session
    paths = visible_sectors(find_sectors(_norm(entry.internal_path) for entry in api.entries))
    sources: dict[Sector, RadarSource] = {}
    for sector, path in paths.items():
        entry = api.get_entry(path)
        if entry is not None:
            sources[sector] = (api.paz_root / entry.archive_name, entry)
    if not sources:
        raise CliError("this PAZ folder has no radar images to build the map from.")
    version = read_meta_version(find_single_meta_file(api.paz_root))
    progress(f"{len(sources):,} radar images, client {version}, {worker_count()} worker processes")
    return sources, version


def _print_progress(state: BuildProgress) -> None:
    if state.done == state.total:
        progress(f"  zoom {state.zoom} ({state.step}/{state.steps}): {state.total:,} tiles")
