"""Row counts a file declares about itself, for `DeclaredCountTest`.

Each helper returns a callable that reads the count from the case's input
bytes, so the expected count follows the fixture through a game update.
A format whose count needs more than these reads defines its own callable in
its test module.
"""
from __future__ import annotations

import struct
from typing import Callable

from .case_input import CaseInput


DeclaredCount = Callable[[CaseInput], int]


def header_count(offset: int = 0, fmt: str = "<I", companion: str | None = None) -> DeclaredCount:
    """The count stored at `offset` of the data file or of `companion`."""

    def read(source: CaseInput) -> int:
        raw = source.file(companion)
        if offset + struct.calcsize(fmt) > len(raw):
            raise AssertionError(f"count at +0x{offset:X} is past the end of {len(raw)} bytes")
        return struct.unpack_from(fmt, raw, offset)[0]

    return read


def fixed_rows(row_size: int, header_size: int = 0, companion: str | None = None) -> DeclaredCount:
    """The number of `row_size` rows after a `header_size` header, which must divide evenly."""

    def read(source: CaseInput) -> int:
        body = len(source.file(companion)) - header_size
        if body < 0 or body % row_size:
            raise AssertionError(
                f"{body} bytes after the {header_size}-byte header are not whole {row_size}-byte rows"
            )
        return body // row_size

    return read
