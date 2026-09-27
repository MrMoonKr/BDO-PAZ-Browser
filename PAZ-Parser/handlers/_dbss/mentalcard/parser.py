"""`mentalcard.dbss`: knowledge cards, located through `mentalcardoffset.dbss`.

The offset file is `PABR`, a u32 count and 12-byte rows (`card_id`,
`data_offset`, `size`). Each record is a 33-byte header followed by a body:

    u32 card_id | u16 theme_id | u8 u8 | f32 min_favor | f32 max_favor
    | f32 interest | u32 flags | u32 u32 | u8
    | name | description | u8 u8 u32 | icon_path | acquisition | f32[3] position
    | u8 u32 | u32 hash_count + hash_count x u32 | u8[5]

Strings are an i64 UTF-16 code-unit count plus UTF-16LE text; the icon path is
an i64 byte count plus ASCII. Full layout in docs/file-formats/mentalcard_dbss.md.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

from _common.pabr_offset import PABR_MAGIC

_OFFSET_HEADER_SIZE = 8
_OFFSET_ROW = struct.Struct("<III")
_HEADER = struct.Struct("<IHBBfffIIIB")
_I64 = struct.Struct("<q")
# u8 body_flag, u8 reserved, u32 body_value
_BODY_FLAGS_SIZE = 6
_POSITION = struct.Struct("<fff")
# u8 tail_kind, u32 tail_value, u32 hash_count
_TAIL_HEAD = struct.Struct("<BII")
_PADDING_SIZE = 5

# Stored icon paths start at "UI_Artwork/", which hangs off ui_texture.
ICON_ROOT = "ui_texture/"


@dataclass(frozen=True)
class MentalCardIndexRow:
    card_id: int
    offset: int
    size: int


@dataclass(frozen=True)
class MentalCardRecord:
    card_id: int
    theme_id: int
    min_favor: float
    max_favor: float
    interest: float
    flags: int
    name_kr: str
    icon_path: str
    acquisition_kr: str
    position: tuple[float, float, float]


def parse_mentalcard_offset_records(data: bytes) -> list[MentalCardIndexRow]:
    """Every index row in file order. Raises ValueError on a bad header."""
    if len(data) < _OFFSET_HEADER_SIZE or data[:4] != PABR_MAGIC:
        raise ValueError("mentalcardoffset.dbss does not start with PABR magic")

    (count,) = struct.unpack_from("<I", data, 4)
    end = _OFFSET_HEADER_SIZE + count * _OFFSET_ROW.size
    if end > len(data):
        raise ValueError(f"mentalcardoffset.dbss declares {count:,} rows but is only {len(data):,} bytes")

    return [
        MentalCardIndexRow(card_id, offset, size)
        for card_id, offset, size in _OFFSET_ROW.iter_unpack(data[_OFFSET_HEADER_SIZE:end])
    ]


class _Reader:
    def __init__(self, data: bytes, pos: int, end: int, card_id: int) -> None:
        self._data, self.pos, self._end, self._card_id = data, pos, end, card_id

    def _need(self, size: int) -> None:
        if self.pos + size > self._end:
            raise ValueError(f"card {self._card_id} runs past its record at 0x{self.pos:X}")

    def skip(self, size: int) -> None:
        self._need(size)
        self.pos += size

    def unpack(self, fmt: struct.Struct) -> tuple:
        self._need(fmt.size)
        values = fmt.unpack_from(self._data, self.pos)
        self.pos += fmt.size
        return values

    def text(self, *, wide: bool) -> str:
        (length,) = self.unpack(_I64)
        size = length * (2 if wide else 1)
        if length < 0:
            raise ValueError(f"card {self._card_id} has a negative string length")
        self._need(size)
        raw = self._data[self.pos:self.pos + size]
        self.pos += size
        return raw.decode("utf-16-le" if wide else "ascii", errors="replace")


def _parse_record(data: bytes, row: MentalCardIndexRow) -> MentalCardRecord:
    end = row.offset + row.size
    reader = _Reader(data, row.offset, end, row.card_id)
    card_id, theme_id, _flag_a, _flag_b, min_favor, max_favor, interest, flags, *_ = reader.unpack(_HEADER)
    if card_id != row.card_id:
        raise ValueError(f"record at 0x{row.offset:X} holds card {card_id}, index says {row.card_id}")

    name_kr = reader.text(wide=True)
    reader.text(wide=True)  # description
    reader.skip(_BODY_FLAGS_SIZE)
    icon_path = reader.text(wide=False)
    acquisition_kr = reader.text(wide=True)
    position = reader.unpack(_POSITION)
    _kind, _value, hash_count = reader.unpack(_TAIL_HEAD)
    reader.skip(4 * hash_count + _PADDING_SIZE)
    if reader.pos != end:
        raise ValueError(f"card {card_id} ends {end - reader.pos} bytes before its index size")

    return MentalCardRecord(
        card_id=card_id,
        theme_id=theme_id,
        min_favor=min_favor,
        max_favor=max_favor,
        interest=interest,
        flags=flags,
        name_kr=name_kr,
        icon_path=f"{ICON_ROOT}{icon_path.lower()}" if icon_path else "",
        acquisition_kr=acquisition_kr,
        position=position,
    )


def parse_mentalcard_records(data: bytes, offset_data: bytes) -> list[MentalCardRecord]:
    """One record per index row, in index order.

    Raises ValueError on the first record that does not end exactly at its
    index size: the layout has changed and later fields would be misread.
    """
    return [_parse_record(data, row) for row in parse_mentalcard_offset_records(offset_data)]
