"""`regioninfo.bss`: the world region table.

    PABR | u32 count | count x (210-byte head + two counted lists + 171-byte tail)
    | string table | u32 string_table_start | u32 0

Records are byte-packed with no alignment, so they are walked, not searched
for. Region names come from LOC type 17 keyed by `region_key`; the string table
holds the Korean source names. Full layout in docs/file-formats/regioninfo_bss.md.
"""

from __future__ import annotations

import struct

from _common.binary import u16, u32
from _common.pabr_strings import TRAILER_SIZE, read_string_table, string_at, string_table_start


_MAGIC = b"PABR"
_HEADER_SIZE = 8
_HEAD_SIZE = 210
_TAIL_SIZE = 171
_KEY_SIZE = 2
_VECTOR_SIZE = 12

# Head field offsets.
_COLOR = 0x02
_REGION_TYPE = 0x06
_NODE_WAR_DAY = 0x07
_IS_DESERT = 0x0F
_TERRITORY_KEY = 0x5A
_NAME_INDEX = 0x5C
_UNKNOWN_NAME_INDEX = 0x60
_CAPITAL_REGION_KEY = 0x64
_REGION_GROUP_KEY = 0x68
_NODE_KEY = 0x6F
# Tail field offset.
_GUILD_WHARF_MANAGER = 0xA9

# Unconfirmed head fields, kept on the record as unknown_<offset> for search
# and CSV export. The remaining tail fields are walked over but not kept.
_UNKNOWN_U8 = (
    0x0B, 0x0C, 0x0D, 0x0E, *range(0x10, 0x1D), 0x1F, 0x25,
    *range(0x36, 0x3B), 0x42, 0x52, 0x73, 0x93, 0xD1,
)
_UNKNOWN_U16 = (0x1D, 0x66, 0x6B)
_UNKNOWN_U32 = (0x20, 0x26, 0x3C, 0x44, 0x54, 0x95, 0xAD, 0xB1, 0xB5)
_UNKNOWN_F32_ARRAYS = {0x2A: 3, 0x77: 3, 0x83: 3, 0x99: 5}
_UNKNOWN_U32_ARRAYS = {0xB9: 6}

# CppEnums.RegionType from global_define_cpp_enum.luac, without the
# "eRegionType_" prefix. The file also uses 7 and 8, which the enum lacks.
REGION_TYPE_NAMES: tuple[str, ...] = (
    "MinorTown", "MainTown", "Hunting", "Siege", "Fortress", "CastleInSiege", "Arena",
)

# CppEnums.VillageSiegeType, without the "eVillageSiegeType_" prefix. The
# value 7 (_Count) marks a region with no node war.
NODE_WAR_DAY_NAMES: tuple[str, ...] = (
    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
)


def _list(data: bytes, pos: int, item_size: int, end: int) -> tuple[int, int]:
    """Count and end offset of the counted list at `pos`."""
    count = u32(data, pos)
    list_end = pos + 4 + item_size * count
    if list_end > end:
        raise ValueError(f"regioninfo.bss list at 0x{pos:X} runs past the records")
    return count, list_end


def _floats(data: bytes, offset: int, count: int) -> list[float]:
    return list(struct.unpack_from(f"<{count}f", data, offset))


def _unknown_fields(data: bytes, head: int) -> dict:
    fields: dict = {f"unknown_{o:02x}": data[head + o] for o in _UNKNOWN_U8}
    fields.update({f"unknown_{o:02x}": u16(data, head + o) for o in _UNKNOWN_U16})
    fields.update({f"unknown_{o:02x}": u32(data, head + o) for o in _UNKNOWN_U32})
    fields.update({
        f"unknown_{o:02x}": _floats(data, head + o, n) for o, n in _UNKNOWN_F32_ARRAYS.items()
    })
    fields.update({
        f"unknown_{o:02x}": list(struct.unpack_from(f"<{n}I", data, head + o))
        for o, n in _UNKNOWN_U32_ARRAYS.items()
    })
    return fields


def _parse_record(data: bytes, head: int, end: int, strings: list[str]) -> tuple[dict, int]:
    """One record and the offset right after it."""
    key_count, keys_end = _list(data, head + _HEAD_SIZE, _KEY_SIZE, end)
    vector_count, vectors_end = _list(data, keys_end, _VECTOR_SIZE, end)
    tail = vectors_end
    if tail + _TAIL_SIZE > end:
        raise ValueError(f"regioninfo.bss record at 0x{head:X} runs past the records")

    record = {
        "region_key": u16(data, head),
        "name_kr": string_at(strings, u32(data, head + _NAME_INDEX)),
        "region_type": data[head + _REGION_TYPE],
        "node_war_day": data[head + _NODE_WAR_DAY],
        "is_desert": data[head + _IS_DESERT],
        "territory_key": data[head + _TERRITORY_KEY],
        "capital_region_key": u16(data, head + _CAPITAL_REGION_KEY),
        "region_group_key": u16(data, head + _REGION_GROUP_KEY),
        "node_key": u16(data, head + _NODE_KEY),
        "guild_wharf_manager_key": u16(data, tail + _GUILD_WHARF_MANAGER),
        "unknown_02": data[head + _COLOR : head + _COLOR + 3].hex(),
        "unknown_60": string_at(strings, u32(data, head + _UNKNOWN_NAME_INDEX)),
        **_unknown_fields(data, head),
        "unknown_d2_keys": list(struct.unpack_from(f"<{key_count}H", data, head + _HEAD_SIZE + 4)),
        "unknown_d2_vectors": [
            _floats(data, keys_end + 4 + i * _VECTOR_SIZE, 3) for i in range(vector_count)
        ],
    }
    return record, tail + _TAIL_SIZE


def parse_regioninfo_records(data: bytes) -> list[dict]:
    """Every region in file order.

    Raises ValueError on a bad magic, or when the walk does not end where the
    string table starts: then the layout has changed and every field is suspect.
    """
    if len(data) < _HEADER_SIZE + TRAILER_SIZE or data[:4] != _MAGIC:
        raise ValueError("regioninfo.bss has invalid magic.")

    strings = read_string_table(data)
    end = string_table_start(data)
    pos = _HEADER_SIZE
    records: list[dict] = []
    for _ in range(u32(data, 4)):
        record, pos = _parse_record(data, pos, end, strings)
        records.append(record)

    if pos != end:
        raise ValueError("regioninfo.bss records do not end where its string table starts")
    return records
