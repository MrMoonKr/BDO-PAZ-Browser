from __future__ import annotations

import struct

import pytest

from _common.prefixed_string import find_prefixed_ascii, read_prefixed_at, read_prefixed_utf16


def _wide(text: str, high_word: int = 0) -> bytes:
    return struct.pack("<II", len(text), high_word) + text.encode("utf-16-le")


def _ascii(text: str) -> bytes:
    return struct.pack("<II", len(text), 0) + text.encode("ascii")


def test_strict_read_returns_the_next_position() -> None:
    data = _wide("Velia") + _ascii("Icon/a.dds")

    name, pos = read_prefixed_at(data, 0, len(data), wide=True)
    icon, end = read_prefixed_at(data, pos, len(data), wide=False)

    assert (name, icon, end) == ("Velia", "Icon/a.dds", len(data))


def test_strict_read_rejects_text_past_the_end() -> None:
    data = _wide("Velia")

    with pytest.raises(ValueError, match="runs past"):
        read_prefixed_at(data, 0, len(data) - 2, wide=True)


def test_lenient_read_matches_the_strict_read() -> None:
    data = b"\xff" * 4 + _wide("Pearl Shop Box")

    assert read_prefixed_utf16(data, 4) == read_prefixed_at(data, 4, len(data), wide=True)[0]


@pytest.mark.parametrize(
    "data",
    [
        _wide("ab"),
        _wide("x" * 201),
        _wide("Velia", high_word=1),
        _wide("Velia")[:-2],
        b"\x05\x00",
    ],
    ids=["too-short", "too-long", "high-word", "truncated", "no-prefix"],
)
def test_lenient_read_returns_empty_for_an_implausible_prefix(data: bytes) -> None:
    assert read_prefixed_utf16(data, 0) == ""


def test_scan_finds_only_confirmed_ascii_strings() -> None:
    # "Loose text" has no prefix in front of it, so it is not a stored string.
    data = _ascii("Icon/a.dds") + b"\x00Loose text\x00" + _ascii("9999")

    assert find_prefixed_ascii(data, 0, len(data)) == ["Icon/a.dds", "9999"]


@pytest.mark.parametrize(
    ("data", "start", "end"),
    [
        (_ascii("Icon/a.dds"), 1, len(_ascii("Icon/a.dds"))),
        (_ascii("Icon/a.dds"), 0, len(_ascii("Icon/a.dds")) - 1),
        (struct.pack("<II", 12, 0) + b"Icon/a.dds\x00\x00", 0, 20),
        (struct.pack("<II", 2, 0) + b"ab\x00", 0, 11),
        (struct.pack("<II", 201, 0) + b"x" * 201, 0, 209),
        (struct.pack("<II", 4, 0) + b"ab\xffd", 0, 12),
    ],
    ids=["prefix-before-start", "text-past-end", "length-past-text", "too-short", "too-long", "not-printable"],
)
def test_scan_skips_a_string_that_does_not_fit(data: bytes, start: int, end: int) -> None:
    assert find_prefixed_ascii(data, start, end) == []


def test_scan_finds_strings_back_to_back_inside_the_range() -> None:
    data = b"\xff" * 3 + _ascii("New_Icon/a.dds") + _ascii("ITEM_BIC_HIT_1") + b"\xff"

    assert find_prefixed_ascii(data, 3, len(data) - 1) == ["New_Icon/a.dds", "ITEM_BIC_HIT_1"]
