"""Icon images: the small PNG an icon cell shows and the larger icon preview.

`thumbnail_data_url()` builds the icon cell thumbnail. `open_image()` and the
preview helpers serve the popup a click on an icon opens: the image scaled to
fit, and for a sprite the cropped region of its sheet.

Most icons are 44 x 44 DXT textures, but some tables show full-size art as
icons: the 2560 x 1440 journal artwork of `questjournalvideoinfo.bss` is a
14 MB uncompressed DDS. Pillow decodes uncompressed DDS pixel by pixel through
its channel masks, about 4 s for that file, so plain 32-bit BGRA and BGRX
textures are wrapped straight into an image instead, which takes milliseconds.
"""

from __future__ import annotations

import base64
import io
import struct

THUMBNAIL_SIZE = (64, 64)
# The popup shows at most this many pixels on the long side, so the 2560 x 1440
# artwork does not cross the JS bridge as a 10 MB data URL.
PREVIEW_MAX_SIDE = 1280

# (x1, y1, x2, y2) in pixels, as the sprite region indexes store it.
Region = tuple[int, int, int, int]

_IMAGE_DATA_MIME_BY_EXT = {
    ".gif": "image/gif",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

_DDS_MAGIC = b"DDS "
_DDS_HEADER_SIZE = 128
# Offsets into the file, magic included.
_DDS_HEIGHT = 12
_DDS_WIDTH = 16
_DDS_PIXEL_FLAGS = 80
_DDS_BIT_COUNT = 88
_DDS_MASKS = 92
_DDPF_ALPHAPIXELS = 0x1
_DDPF_RGB = 0x40
_BGR_MASKS = (0x00FF0000, 0x0000FF00, 0x000000FF)
_ALPHA_MASK = 0xFF000000


class ThumbnailError(Exception):
    """The payload is not an image this app can decode."""


def _raw_bgra_mode(data: bytes) -> str | None:
    """Pillow raw mode of an uncompressed 32-bit DDS, or None for any other kind."""
    if len(data) < _DDS_HEADER_SIZE or data[:4] != _DDS_MAGIC:
        return None

    (flags,) = struct.unpack_from("<I", data, _DDS_PIXEL_FLAGS)
    (bit_count,) = struct.unpack_from("<I", data, _DDS_BIT_COUNT)
    red, green, blue, alpha = struct.unpack_from("<4I", data, _DDS_MASKS)
    if not flags & _DDPF_RGB or bit_count != 32 or (red, green, blue) != _BGR_MASKS:
        return None
    if flags & _DDPF_ALPHAPIXELS:
        return "BGRA" if alpha == _ALPHA_MASK else None
    return "BGRX"


def open_image(data: bytes):
    """A Pillow RGBA image of an image payload, with the fast path for raw BGRA DDS."""
    from PIL import Image

    mode = _raw_bgra_mode(data)
    if mode is not None:
        (height,) = struct.unpack_from("<I", data, _DDS_HEIGHT)
        (width,) = struct.unpack_from("<I", data, _DDS_WIDTH)
        pixels_end = _DDS_HEADER_SIZE + width * height * 4
        if pixels_end <= len(data):
            return Image.frombuffer(
                "RGBA", (width, height), data[_DDS_HEADER_SIZE:pixels_end], "raw", mode, 0, 1
            )

    return Image.open(io.BytesIO(data)).convert("RGBA")


def thumbnail_data_url(data: bytes, extension: str) -> str:
    """A data URL for an icon cell: web images as they are, anything else as a PNG thumbnail.

    Raises ThumbnailError when Pillow is missing or cannot read the payload.
    """
    mime = _IMAGE_DATA_MIME_BY_EXT.get(extension.lower())
    if mime is not None:
        return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"

    try:
        import PIL  # noqa: F401
    except ImportError as ex:
        raise ThumbnailError("Pillow not installed") from ex

    try:
        img = open_image(data)
        img.thumbnail(THUMBNAIL_SIZE)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
    except Exception as ex:
        raise ThumbnailError(str(ex)) from ex
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"


def png_data_url(img) -> str:
    buf = io.BytesIO()
    # Level 1 keeps a full-size preview quick to encode; the size difference is small.
    img.save(buf, format="PNG", compress_level=1)
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"


def preview_data_url(img) -> str:
    """The image scaled down to PREVIEW_MAX_SIDE when larger, as a PNG data URL."""
    if max(img.size) <= PREVIEW_MAX_SIDE:
        return png_data_url(img)
    scaled = img.copy()
    scaled.thumbnail((PREVIEW_MAX_SIDE, PREVIEW_MAX_SIDE))
    return png_data_url(scaled)


def checked_region(region: object, size: tuple[int, int]) -> Region:
    """`region` as four ints inside an image of `size`.

    Raises ValueError for anything else: the region comes from the page, and a
    crop outside the sheet would silently pad with black.
    """
    if not isinstance(region, (list, tuple)) or len(region) != 4:
        raise ValueError(f"Sprite region must be four numbers, got {region!r}")
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in region):
        raise ValueError(f"Sprite region must be whole numbers, got {region!r}")

    x1, y1, x2, y2 = region
    width, height = size
    if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
        raise ValueError(f"Sprite region {tuple(region)} is outside the {width} x {height} sheet")
    return x1, y1, x2, y2


def sprite_data_url(img, region: Region) -> str:
    """The sprite at its own size, cropped from its sheet."""
    return png_data_url(img.crop(region))
