"""Unit tests for DeclaredCountTest and the declared-count builders."""
from __future__ import annotations

import struct

import pytest

from tests.framework import CaseInput, DeclaredCountTest, fixed_rows, header_count


def _source(data: bytes, **companions: bytes) -> CaseInput:
    return CaseInput(data=data, companions=companions)


def test_header_count_reads_the_data_file() -> None:
    source = _source(struct.pack("<HI", 0xFFFF, 3))
    assert header_count(offset=2)(source) == 3


def test_header_count_reads_a_companion_with_its_format() -> None:
    source = _source(b"", **{"x_offset.dbss": struct.pack("<H", 7)})
    assert header_count(fmt="<H", companion="x_offset.dbss")(source) == 7


def test_header_count_past_the_end_fails() -> None:
    with pytest.raises(AssertionError, match="past the end"):
        header_count(offset=2)(_source(b"\x01\x00"))


def test_missing_companion_fails() -> None:
    with pytest.raises(AssertionError, match="no companion"):
        header_count(companion="absent.dbss")(_source(b"\x00" * 4))


def test_fixed_rows_counts_rows_after_the_header() -> None:
    assert fixed_rows(row_size=6, header_size=4)(_source(b"\x00" * 16)) == 2


@pytest.mark.parametrize("size", [3, 15])
def test_fixed_rows_rejects_a_partial_row_or_short_header(size: int) -> None:
    with pytest.raises(AssertionError, match="not whole"):
        fixed_rows(row_size=6, header_size=4)(_source(b"\x00" * size))


def test_declared_count_passes_on_a_match() -> None:
    spec = DeclaredCountTest(declared=header_count())
    assert "2" in spec.check([{}, {}], _source(struct.pack("<I", 2)))


def test_declared_count_fails_on_a_mismatch() -> None:
    spec = DeclaredCountTest(declared=header_count())
    with pytest.raises(AssertionError, match="declares 3 rows, parsed 2"):
        spec.check([{}, {}], _source(struct.pack("<I", 3)))
