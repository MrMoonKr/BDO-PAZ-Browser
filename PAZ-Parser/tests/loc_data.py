"""Build small `languagedata_*.loc` files for tests."""
from __future__ import annotations

import struct
import zlib

# (str_type, str_id1, str_id2, str_id3, str_id4, text)
LocRow = tuple[int, int, int, int, int, str]


def loc_bytes(rows: list[LocRow]) -> bytes:
    """A LOC file holding `rows` in order, as `init_loc()` reads it."""
    body = b"".join(
        struct.pack("<IIIHBB", len(text), str_type, id1, id2, id3, id4)
        + text.encode("utf-16-le")
        + b"\0\0\0\0"
        for str_type, id1, id2, id3, id4, text in rows
    )
    return struct.pack("<I", len(body)) + zlib.compress(body)
