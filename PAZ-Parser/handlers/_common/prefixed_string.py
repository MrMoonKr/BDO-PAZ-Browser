"""Length-prefixed strings embedded in variable-length DBSS blocks.

Several large tables store text inline with an 8-byte prefix: a u32 length
followed by a u32 zero, then the text itself with no terminator. UTF-16 strings
count characters, ASCII strings count bytes.

`read_prefixed_at` is the one decoder: strict, for a prefix at a known position,
and it returns where the next field starts. The lenient readers are for strings
whose position is only a guess, so they also require a plausible prefix (3 to
200 units, zero high word) and return nothing instead of raising:
`read_prefixed_utf16` checks one candidate position, and `find_prefixed_ascii`
locates ASCII text by scanning printable runs and confirming the length that
precedes each candidate.
"""

from __future__ import annotations

import re

from _common.binary import u32


STRING_PREFIX_SIZE = 8

_MIN_LENGTH = 3
_MAX_LENGTH = 200

_PRINTABLE_RUN = re.compile(rb"[ -~]{3,200}")


def _is_plausible_prefix(data: bytes, prefix_at: int) -> bool:
    """Whether `prefix_at` holds a short-string length with a zero high word.

    For reads that only guess where a string sits, where a real prefix must be
    told apart from arbitrary bytes.
    """
    return (
        _MIN_LENGTH <= u32(data, prefix_at) <= _MAX_LENGTH
        and u32(data, prefix_at + 4) == 0
    )


def read_prefixed_utf16(data: bytes, prefix_at: int) -> str:
    """Read a UTF-16LE string whose 8-byte prefix may start at `prefix_at`.

    The lenient form of `read_prefixed_at`, for a string that is not always
    there: returns an empty string when the prefix is not a plausible header
    (3 to 200 characters) or the text runs past the buffer.
    """
    if not _is_plausible_prefix(data, prefix_at):
        return ""

    try:
        text, _ = read_prefixed_at(data, prefix_at, len(data), wide=True)
    except ValueError:
        return ""
    return text


def find_prefixed_ascii(data: bytes, start: int, end: int) -> list[str]:
    """Return every length-prefixed ASCII string inside `[start, end)`.

    Candidates come from printable runs and are confirmed against the u32 length
    stored 8 bytes before the text.
    """
    found: list[str] = []

    for match in _PRINTABLE_RUN.finditer(data, start, end):
        text_start = match.start()
        prefix_at = text_start - STRING_PREFIX_SIZE
        if prefix_at < start or not _is_plausible_prefix(data, prefix_at):
            continue

        length = u32(data, prefix_at)
        if length > match.end() - text_start or text_start + length > end:
            continue

        found.append(data[text_start:text_start + length].decode("ascii"))

    return found


def read_prefixed_at(
    data: bytes,
    prefix_at: int,
    end: int,
    *,
    wide: bool,
) -> tuple[str, int]:
    """Read a string whose prefix sits at a known position, with no length cap.

    For tables that chain strings back to back, where each read must return the
    position of the next field. `wide` selects UTF-16LE (length in characters)
    over ASCII (length in bytes). Raises ValueError when the prefix is malformed
    or the text would run past `end`, since every later field would be misread.
    """
    if prefix_at + STRING_PREFIX_SIZE > end:
        raise ValueError(f"string prefix at 0x{prefix_at:X} runs past 0x{end:X}")

    length = u32(data, prefix_at)
    if u32(data, prefix_at + 4) != 0:
        raise ValueError(f"string prefix at 0x{prefix_at:X} has a non-zero high word")

    start = prefix_at + STRING_PREFIX_SIZE
    text_end = start + length * (2 if wide else 1)
    if text_end > end:
        raise ValueError(f"string at 0x{start:X} runs past 0x{end:X}")

    encoding = "utf-16-le" if wide else "ascii"
    return data[start:text_end].decode(encoding, errors="replace"), text_end
