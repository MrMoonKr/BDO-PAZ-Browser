"""`init_loc()`: reading a LOC file into the key index and the prefix lists."""
from __future__ import annotations

import zlib
from collections.abc import Iterator

import pytest

import _common.loc as loc
from tests.loc_counter import reset_loc
from tests.loc_data import LocRow, loc_bytes

_ROWS: list[LocRow] = [
    (50, 114415, 0, 12, 0, "Gloves"),
    (6, 300, 0, 0, 0, "gamma"),
    (50, 114415, 0, 12, 3, "Contains"),
    (24, 70000, 513, 255, 7, "full key"),
]


@pytest.fixture(autouse=True)
def _clear_loc() -> Iterator[None]:
    reset_loc()
    yield
    reset_loc()


def test_every_field_of_the_key_finds_its_text() -> None:
    loc.init_loc(loc_bytes(_ROWS))

    assert loc.loc_lookup(24, 70000, 513, 255, 7) == "full key"
    assert loc.loc_lookup(6, 300) == "gamma"
    assert loc.loc_lookup(24, 70000) == ""


def test_prefix_lists_keep_file_order() -> None:
    loc.init_loc(loc_bytes(_ROWS))

    assert loc.loc_lookup_prefix(50, 114415) == ["Gloves", "Contains"]
    assert loc.loc_lookup_prefix(6, 300) == ["gamma"]


def test_a_truncated_last_record_is_left_out() -> None:
    whole = loc.decompress_loc(loc_bytes(_ROWS))
    assert whole is not None
    cut = loc_bytes(_ROWS[:1])[:4] + zlib.compress(whole[:-6])

    loc.init_loc(cut)

    assert loc.loc_lookup(6, 300) == "gamma"
    assert loc.loc_lookup(24, 70000, 513, 255, 7) == ""


def test_invalid_utf16_is_replaced() -> None:
    raw = loc_bytes([(6, 1, 0, 0, 0, "ab")])
    body = bytearray(loc.decompress_loc(raw) or b"")
    body[16:18] = b"\x00\xd8"  # a lone high surrogate in place of "a"

    loc.init_loc(raw[:4] + zlib.compress(bytes(body)))

    assert loc.loc_lookup(6, 1) == "\ufffdb"



def test_records_split_across_stream_pieces_are_read_whole(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(loc, "_STREAM_CHUNK_BYTES", 3)

    loc.init_loc(loc_bytes(_ROWS))

    assert loc.loc_lookup(24, 70000, 513, 255, 7) == "full key"
    assert loc.loc_lookup_prefix(50, 114415) == ["Gloves", "Contains"]


def test_a_truncated_zlib_stream_loads_no_text() -> None:
    raw = loc_bytes(_ROWS)

    loc.init_loc(raw[:-5])

    assert not loc.is_loc_loaded()


def test_decompress_loc_returns_the_record_stream() -> None:
    raw = loc_bytes(_ROWS)

    assert loc.decompress_loc(raw) == zlib.decompress(raw[4:])
    assert loc.decompress_loc(raw[:3]) is None
    assert loc.decompress_loc(raw[:4] + b"not zlib") is None
