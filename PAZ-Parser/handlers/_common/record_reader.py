"""Sequential reader over one variable-length record.

Many DBSS records are a run of fixed fields and length-prefixed strings: a u64
unit count followed by that many UTF-16LE code units (text and scripts) or
single-byte ASCII characters (paths and internal names), with no terminator.
The reader walks such a record from its start and raises ValueError as soon as
a field would run past the record, so a changed layout fails loudly instead of
misreading every later field.
"""

from __future__ import annotations

import struct

_U64 = struct.Struct("<Q")


class RecordReader:
    """Reads fields of the record `data[start:end]` in order.

    `label` names the record in error messages, e.g. "card 3030".
    """

    def __init__(self, data: bytes, start: int, end: int, label: str) -> None:
        if end > len(data):
            raise ValueError(f"{label} ends at 0x{end:X}, past the {len(data):,}-byte file")
        self._data, self.pos, self._end, self._label = data, start, end, label

    def _take(self, size: int) -> bytes:
        stop = self.pos + size
        if stop > self._end:
            raise ValueError(f"{self._label} runs past its record at 0x{self.pos:X}")
        raw = self._data[self.pos:stop]
        self.pos = stop
        return raw

    def skip(self, size: int) -> None:
        self._take(size)

    def unpack(self, fmt: struct.Struct) -> tuple:
        return fmt.unpack(self._take(fmt.size))

    def text(self, *, wide: bool) -> str:
        """A u64-prefixed string: UTF-16LE when `wide`, else ASCII."""
        (length,) = self.unpack(_U64)
        raw = self._take(length * (2 if wide else 1))
        return raw.decode("utf-16-le" if wide else "ascii", errors="replace")

    def remaining(self) -> int:
        return self._end - self.pos

    def at_end(self) -> bool:
        return self.pos == self._end
