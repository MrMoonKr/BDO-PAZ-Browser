"""Icon cell thumbnails: an image payload turned into a small PNG data URL.

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


def _open_image(data: bytes):
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
        img = _open_image(data)
        img.thumbnail(THUMBNAIL_SIZE)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
    except Exception as ex:
        raise ThumbnailError(str(ex)) from ex
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"
