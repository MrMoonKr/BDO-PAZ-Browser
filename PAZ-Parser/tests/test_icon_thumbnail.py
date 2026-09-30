from __future__ import annotations

import base64
import io
import struct

import pytest

from api.bdo_icon_thumbnail import THUMBNAIL_SIZE, ThumbnailError, _raw_bgra_mode, thumbnail_data_url

Image = pytest.importorskip("PIL.Image")

_DDSD_FLAGS = 0x1007  # caps | height | width | pixel format
_DDPF_ALPHAPIXELS = 0x1
_DDPF_RGB = 0x40
_BGRA_MASKS = (0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)


def _dds(width: int, height: int, pixels_bgra: bytes, *, alpha: bool = True, bits: int = 32) -> bytes:
    """An uncompressed DDS with the header layout the client uses."""
    pf_flags = _DDPF_RGB | (_DDPF_ALPHAPIXELS if alpha else 0)
    masks = _BGRA_MASKS if alpha else _BGRA_MASKS[:3] + (0,)
    header = struct.pack("<4sII", b"DDS ", 124, _DDSD_FLAGS)
    header += struct.pack("<II", height, width) + bytes(4 * 3) + bytes(44)
    header += struct.pack("<II4sI4I", 32, pf_flags, bytes(4), bits, *masks)
    header += bytes(128 - len(header))
    assert len(header) == 128
    return header + pixels_bgra


def _png_pixels(url: str) -> tuple[tuple[int, int], bytes]:
    img = Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))).convert("RGBA")
    return img.size, img.tobytes()


# Two pixels: opaque red, half-transparent blue, stored as BGRA.
_PIXELS = bytes([0, 0, 255, 255, 255, 0, 0, 128])


def test_uncompressed_dds_takes_the_fast_path() -> None:
    assert _raw_bgra_mode(_dds(2, 1, _PIXELS)) == "BGRA"
    assert _raw_bgra_mode(_dds(2, 1, _PIXELS, alpha=False)) == "BGRX"


def test_other_pixel_formats_fall_back_to_pillow() -> None:
    assert _raw_bgra_mode(_dds(2, 1, _PIXELS, bits=24)) is None
    assert _raw_bgra_mode(b"\x89PNG" + bytes(200)) is None


def test_fast_path_matches_pillow() -> None:
    data = _dds(2, 1, _PIXELS)
    expected = Image.open(io.BytesIO(data)).convert("RGBA")

    size, pixels = _png_pixels(thumbnail_data_url(data, ".dds"))

    assert size == expected.size
    assert pixels == expected.tobytes() == bytes([255, 0, 0, 255, 0, 0, 255, 128])


def test_large_textures_shrink_to_the_thumbnail_size() -> None:
    data = _dds(256, 128, bytes(256 * 128 * 4))

    size, _ = _png_pixels(thumbnail_data_url(data, ".dds"))

    assert max(size) == max(THUMBNAIL_SIZE)


def test_web_images_are_passed_through() -> None:
    assert thumbnail_data_url(b"GIF89a", ".GIF") == "data:image/gif;base64,R0lGODlh"


def test_unreadable_payload_raises() -> None:
    with pytest.raises(ThumbnailError):
        thumbnail_data_url(b"not an image", ".dds")
