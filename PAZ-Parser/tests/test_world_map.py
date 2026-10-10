from __future__ import annotations

import pytest

from world_map import (
    MAX_ZOOM,
    MIN_ZOOM,
    RADAR_FOLDER,
    SEA_FILLER_SECTORS,
    SEA_VARIANTS,
    SECTOR_CM,
    SECTOR_PX,
    TILE_PX,
    child_tiles,
    HIDDEN_SECTORS,
    filler_sector,
    find_sectors,
    is_hidden,
    native_tile,
    parent_tile,
    pyramid,
    sea_parts,
    sea_variant,
    tile_sectors,
    visible_sectors,
    world_bounds,
)


def _radar(x: int, y: int, folder: str = RADAR_FOLDER) -> str:
    return f"{folder}/rader_{x}_{y}.dds"


def _leaflet_tile(world_x: float, world_z: float) -> tuple[int, int]:
    """The MAX_ZOOM tile Leaflet asks for at a world point, with map-view.js's world CRS."""
    pixel_x = world_x / SECTOR_CM * SECTOR_PX
    pixel_y = -world_z / SECTOR_CM * SECTOR_PX
    return int(pixel_x // TILE_PX), int(pixel_y // TILE_PX)


def test_find_sectors_reads_only_the_radar_pack() -> None:
    sectors = find_sectors([
        _radar(-134, 140),
        _radar(3, -2),
        _radar(5, 5, "ui_texture/new_ui_common_forlua/widget/rader/minimap_data"),
        _radar(1, 1, f"{RADAR_FOLDER}/_morningland"),
        "ui_texture/new_ui_common_forlua/widget/rader/rader_ocean_0_0.dds",
    ])

    assert sectors == {(-134, 140): _radar(-134, 140), (3, -2): _radar(3, -2)}


@pytest.mark.parametrize(
    ("world_x", "world_z"),
    [(1.0, 1.0), (13800.0, 76996.0), (-1524540.0, 1696590.0), (12799.0, -1.0), (-1.0, -657172.0)],
)
def test_a_world_point_lies_in_a_sector_of_the_tile_leaflet_asks_for(world_x: float, world_z: float) -> None:
    sector = (int(world_x // SECTOR_CM), int(world_z // SECTOR_CM))
    tile = _leaflet_tile(world_x, world_z)

    assert native_tile(sector) == tile
    assert sector in tile_sectors(tile)


def test_tile_sectors_put_north_at_the_top() -> None:
    top_left, top_right, bottom_left, bottom_right = tile_sectors((0, 0))

    assert (top_left, top_right) == ((0, -1), (1, -1))
    assert (bottom_left, bottom_right) == ((0, -2), (1, -2))


@pytest.mark.parametrize("tile", [(0, 0), (-1, -1), (5, -8), (-67, 70)])
def test_a_tile_is_one_of_its_parents_children(tile: tuple[int, int]) -> None:
    assert tile in child_tiles(parent_tile(tile))
    assert all(parent_tile(child) == tile for child in child_tiles(tile))


def test_pyramid_has_every_zoom_and_each_tile_has_its_parent() -> None:
    levels = pyramid([(-134, 140), (0, 0), (114, -75)])

    assert sorted(levels) == list(range(MIN_ZOOM, MAX_ZOOM + 1))
    for zoom in range(MIN_ZOOM + 1, MAX_ZOOM + 1):
        assert {parent_tile(tile) for tile in levels[zoom]} == levels[zoom - 1]


def test_world_bounds_span_whole_sectors() -> None:
    bounds = world_bounds([(-2, 3), (1, -1)])

    assert bounds is not None
    assert (bounds.min_x, bounds.max_x) == (-2 * SECTOR_CM, 2 * SECTOR_CM)
    assert (bounds.min_z, bounds.max_z) == (-1 * SECTOR_CM, 4 * SECTOR_CM)
    assert world_bounds([]) is None


def test_filler_and_sea_picks_are_stable_and_in_range() -> None:
    sector = (-50, 12)

    assert filler_sector(sector) == filler_sector(sector)
    assert filler_sector(sector) in SEA_FILLER_SECTORS
    assert 0 <= sea_variant(5, (3, -4)) < SEA_VARIANTS
    assert sea_variant(5, (3, -4)) == sea_variant(5, (3, -4))
    assert all(0 <= part < len(SEA_FILLER_SECTORS) for part in sea_parts(MAX_ZOOM, 0))
    assert all(0 <= part < SEA_VARIANTS for part in sea_parts(MAX_ZOOM - 1, 0))


def test_hidden_sectors_are_left_out_and_range_ends_count() -> None:
    min_x, min_y, max_x, max_y = HIDDEN_SECTORS[0]
    inside = {(min_x, min_y): "a", (max_x, max_y): "b"}
    outside = (max_x + 1, max_y + 1)

    assert all(is_hidden(sector) for sector in inside)
    assert visible_sectors({**inside, outside: "c"}) == ({outside: "c"} if not is_hidden(outside) else {})


def test_no_sea_filler_sector_is_hidden() -> None:
    assert not any(is_hidden(sector) for sector in SEA_FILLER_SECTORS)
