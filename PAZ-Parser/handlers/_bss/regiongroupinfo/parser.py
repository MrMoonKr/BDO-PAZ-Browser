"""`regiongroupinfo.bss`: the region groups that `regioninfo.bss` regions join.

    PABR | u32 count | count x 51-byte row | u32 0 (empty string table)
    | u32 string_table_start | u32 0

Rows are byte-packed, so fields sit at odd offsets. Each row names the
worldmap node (LOC type 29) of the group's main region and a world position.
Full layout in docs/file-formats/regiongroupinfo_bss.md.
"""

from __future__ import annotations

from _common.binary import f32, u8, u16, u32
from _common.pabr_strings import fixed_row_offsets, string_table_start


ROW_SIZE = 51

# Row field offsets.
_REGION_GROUP_KEY = 0x00
_UNKNOWN_03 = 0x03
_NODE_KEY = 0x05
_UNKNOWN_09 = 0x09
_UNKNOWN_0A = 0x0A
_UNKNOWN_0B = 0x0B
_POSITION = 0x0C
_UNKNOWN_19 = 0x19
_UNKNOWN_1D = 0x1D
_UNKNOWN_21 = 0x21
_UNKNOWN_31 = 0x31

_AXES = ("pos_x", "pos_y", "pos_z")
_AXIS_SIZE = 4


def _position(data: bytes, pos: int) -> dict[str, float | None]:
    """The world position, or None on every axis for the all-zero "none" value."""
    axes = [f32(data, pos + _POSITION + i * _AXIS_SIZE) for i in range(len(_AXES))]
    if not any(axes):
        return dict.fromkeys(_AXES)
    return dict(zip(_AXES, axes))


def _parse_row(data: bytes, pos: int) -> dict:
    node_key = u16(data, pos + _NODE_KEY)
    return {
        "region_group_key": u16(data, pos + _REGION_GROUP_KEY),
        "node_key": node_key or None,
        **_position(data, pos),
        "unknown_03": u16(data, pos + _UNKNOWN_03),
        "unknown_09": u8(data, pos + _UNKNOWN_09),
        "unknown_0a": u8(data, pos + _UNKNOWN_0A),
        "unknown_0b": u8(data, pos + _UNKNOWN_0B),
        "unknown_19": u32(data, pos + _UNKNOWN_19),
        "unknown_1d": u32(data, pos + _UNKNOWN_1D),
        "unknown_21": u32(data, pos + _UNKNOWN_21),
        "unknown_31": u8(data, pos + _UNKNOWN_31),
    }


def parse_regiongroupinfo_records(data: bytes) -> list[dict]:
    """Every row in file order.

    Raises ValueError on a missing magic or a row count that does not end
    where the trailer says the string table starts.
    """
    return [_parse_row(data, pos) for pos in fixed_row_offsets(data, ROW_SIZE, "regiongroupinfo.bss")]
