"""Counted string table at the end of a PABR `.bss` file.

    ... rows ... | u32 count | count x (u8 is_wide | u32 byte_length | payload)
    | u32 string_table_start | u32 0

Wide entries are UTF-16LE, the rest UTF-8. Records point into the table by
index. `exploration.bss` and `npcsimply.bss` share this tail.
"""

from __future__ import annotations

from _common.binary import u32


TRAILER_SIZE = 8

_ENTRY_HEADER_SIZE = 5


def string_table_start(data: bytes) -> int:
    """Offset stored in the 8-byte trailer, where the rows end."""
    return u32(data, len(data) - TRAILER_SIZE)


def read_string_table(data: bytes) -> list[str]:
    """Every string in table order.

    Raises ValueError when an entry runs into the trailer, since every later
    index would then point at the wrong text.
    """
    end = len(data) - TRAILER_SIZE
    start = string_table_start(data)
    if not 0 <= start <= end - 4:
        raise ValueError(f"string table offset 0x{start:X} is outside the file")

    count = u32(data, start)
    pos = start + 4
    strings: list[str] = []
    for _ in range(count):
        is_wide, length = data[pos], u32(data, pos + 1)
        text_start = pos + _ENTRY_HEADER_SIZE
        pos = text_start + length
        if pos > end:
            raise ValueError(f"string at 0x{text_start:X} runs past the string table")
        encoding = "utf-16-le" if is_wide else "utf-8"
        strings.append(data[text_start:pos].decode(encoding, errors="replace"))
    return strings


def string_at(strings: list[str], index: int) -> str:
    """The string at `index`, or an empty string when it is out of range."""
    return strings[index] if 0 <= index < len(strings) else ""
