from __future__ import annotations

import argparse
import io
from pathlib import Path

import pytest

import bdo_app
from world_map import SECTOR_PX
from world_map_build import MANIFEST_NAME
from world_map_export import TILES_FOLDER, ExportError, export_image, export_tiles, image_name

Image = pytest.importorskip("PIL.Image")

RED = (200, 0, 0)
BLUE = (0, 0, 200)


def _png(color: tuple[int, int, int]) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (SECTOR_PX, SECTOR_PX), color).save(buf, format="PNG")
    return buf.getvalue()


def _same(data: bytes) -> bytes:
    return data


def _quiet(_progress: object) -> None:
    pass


def _near(pixel: tuple[int, int, int], color: tuple[int, int, int]) -> bool:
    return all(abs(a - b) <= 24 for a, b in zip(pixel, color))  # JPEG is lossy


def test_the_image_puts_each_sector_north_up_at_its_place(tmp_path: Path) -> None:
    # (0, 0) is north-west of (1, -1): top-left and bottom-right of a 2 x 2 sector map.
    sectors = {(0, 0): _png(RED), (1, -1): _png(BLUE)}

    path = export_image(
        sectors=sectors, read=_same, folder=tmp_path, version=1, workers=0, zoom=4, on_progress=_quiet
    )

    assert path == tmp_path / image_name(4)
    with Image.open(path) as image:
        assert image.size == (32, 32)  # 2 sectors of 16 px at zoom 4
        assert _near(image.convert("RGB").getpixel((4, 4)), RED)
        assert _near(image.convert("RGB").getpixel((28, 28)), BLUE)
    assert [p.name for p in tmp_path.iterdir()] == [image_name(4)]


def test_tiles_of_one_zoom_keep_only_that_zoom(tmp_path: Path) -> None:
    target, manifest = export_tiles(
        sectors={(0, -1): _png(RED)}, read=_same, folder=tmp_path, version=1, workers=0, zoom=7, on_progress=_quiet
    )

    assert target == tmp_path / TILES_FOLDER
    assert sorted(p.name for p in target.iterdir()) == ["7", MANIFEST_NAME, "sea"]
    assert [p.name for p in (target / "sea").iterdir()] == ["7"]
    assert manifest.tiles > 0


def test_tiles_refuse_to_replace_a_folder_that_is_no_export(tmp_path: Path) -> None:
    (tmp_path / TILES_FOLDER).mkdir()
    (tmp_path / TILES_FOLDER / "notes.txt").write_text("mine")

    with pytest.raises(ExportError):
        export_tiles(
            sectors={(0, -1): _png(RED)}, read=_same, folder=tmp_path, version=1, workers=0, zoom=7, on_progress=_quiet
        )
    assert (tmp_path / TILES_FOLDER / "notes.txt").exists()


def _parse(*argv: str) -> argparse.Namespace:
    parser = bdo_app._build_parser()
    args = parser.parse_args(list(argv))
    bdo_app._check_options(parser, args)
    return args


def test_map_commands_need_dir_and_zoom_needs_a_map_command() -> None:
    assert _parse("--map-tiles", "--dir", "out", "--zoom", "7").zoom == 7
    with pytest.raises(SystemExit):
        _parse("--map-image")
    with pytest.raises(SystemExit):
        _parse("--list", "x", "--zoom", "3")
    with pytest.raises(SystemExit):
        _parse("--map-image", "--dir", "out", "--zoom", "8")
