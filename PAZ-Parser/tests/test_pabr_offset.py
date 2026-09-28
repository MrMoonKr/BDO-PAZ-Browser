from __future__ import annotations

import struct

import pytest

from _common.pabr_offset import PabrOffsetRow, parse_bare_offset_rows, parse_pabr_offset_rows

_ROWS = [PabrOffsetRow(9, 0x06, 406), PabrOffsetRow(8, 0x19E, 406)]
_TRAILER = bytes(12)


def _row_bytes(rows: list[PabrOffsetRow]) -> bytes:
    return b"".join(struct.pack("<HII", r.entry_id, r.offset, r.size) for r in rows)


def _count(rows: list[PabrOffsetRow]) -> bytes:
    return struct.pack("<I", len(rows))


def test_pabr_table_reads_rows_after_the_magic() -> None:
    data = b"PABR" + _count(_ROWS) + _row_bytes(_ROWS) + _TRAILER

    assert parse_pabr_offset_rows(data) == _ROWS


def test_pabr_table_without_magic_is_rejected() -> None:
    with pytest.raises(ValueError, match="PABR magic"):
        parse_pabr_offset_rows(_count(_ROWS) + _row_bytes(_ROWS))


def test_bare_table_reads_rows_after_the_count() -> None:
    assert parse_bare_offset_rows(_count(_ROWS) + _row_bytes(_ROWS)) == _ROWS


@pytest.mark.parametrize(
    "data",
    [
        b"PABR" + _count(_ROWS) + _row_bytes(_ROWS[:1]),
        _count(_ROWS) + _row_bytes(_ROWS[:1]),
    ],
    ids=["pabr", "bare"],
)
def test_count_past_the_end_is_rejected(data: bytes) -> None:
    parse = parse_pabr_offset_rows if data.startswith(b"PABR") else parse_bare_offset_rows

    with pytest.raises(ValueError, match="only has room for 1"):
        parse(data)


def test_bare_table_too_short_for_its_count_is_rejected() -> None:
    with pytest.raises(ValueError, match="too short"):
        parse_bare_offset_rows(b"\x01\x00")
