from __future__ import annotations

import struct

import pytest

from _common.pabr_strings import (
    HEADER_SIZE,
    check_rows_end,
    checked_string_table_start,
    fixed_row_offsets,
)

_ROW_SIZE = 6
_EMPTY_STRING_TABLE = struct.pack("<I", 0)


def _pabr(row_count: int, row_bytes: int) -> bytes:
    """A PABR file with `row_bytes` of rows, an empty string table and the trailer."""
    table_start = HEADER_SIZE + row_bytes
    return (
        b"PABR"
        + struct.pack("<I", row_count)
        + bytes(row_bytes)
        + _EMPTY_STRING_TABLE
        + struct.pack("<II", table_start, 0)
    )


def test_fixed_row_offsets_starts_every_row_after_the_header() -> None:
    offsets = fixed_row_offsets(_pabr(3, 3 * _ROW_SIZE), _ROW_SIZE, "test.bss")

    assert list(offsets) == [HEADER_SIZE, HEADER_SIZE + _ROW_SIZE, HEADER_SIZE + 2 * _ROW_SIZE]


def test_fixed_row_offsets_rejects_rows_that_miss_the_string_table() -> None:
    with pytest.raises(ValueError, match="test.bss rows end at .* string table starts"):
        fixed_row_offsets(_pabr(3, 3 * _ROW_SIZE + 1), _ROW_SIZE, "test.bss")


def test_fixed_row_offsets_rejects_a_bad_magic() -> None:
    data = b"XXXX" + _pabr(1, _ROW_SIZE)[4:]

    with pytest.raises(ValueError, match="test.bss has invalid magic"):
        fixed_row_offsets(data, _ROW_SIZE, "test.bss")


def test_check_rows_end_accepts_the_string_table_start() -> None:
    data = _pabr(2, 2 * _ROW_SIZE)

    check_rows_end(data, HEADER_SIZE + 2 * _ROW_SIZE, "test.bss records")


def test_checked_string_table_start_rejects_an_offset_outside_the_file() -> None:
    data = _pabr(0, 0)[:-8] + struct.pack("<II", 0xFFFF, 0)

    with pytest.raises(ValueError, match="outside the file"):
        checked_string_table_start(data, "test.bss")
