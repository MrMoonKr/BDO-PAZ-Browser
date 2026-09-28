from __future__ import annotations

import struct

from _common.pabr_offset import parse_bare_offset_rows


# petexp.dbss opens with a u32 record count.
_DATA_HEADER_SIZE = 4
# Each offset points just past a u16 copy of the EXP table ID.
_KEY_PREFIX_SIZE = 2
_PAYLOAD_SIZE = 406
_LEVEL_CAPACITY = 50


def parse_petexpoffset_records(data: bytes) -> list[dict]:
    return [
        {
            "exp_table_id": row.entry_id,
            "data_offset": row.offset,
            "data_size": row.size,
            "record_start": row.offset - _KEY_PREFIX_SIZE,
        }
        for row in parse_bare_offset_rows(data)
    ]


def parse_petexp_records(data: bytes, offset_data: bytes) -> list[dict]:
    records: list[dict] = []

    for row, offset_row in enumerate(parse_bare_offset_rows(offset_data)):
        data_offset = offset_row.offset
        data_size = offset_row.size
        record_start = data_offset - _KEY_PREFIX_SIZE
        if record_start < _DATA_HEADER_SIZE or data_offset + data_size > len(data):
            raise ValueError(f"pet exp record {row} exceeds file size")
        if data_size < _PAYLOAD_SIZE:
            raise ValueError(f"pet exp record {row} payload is too small")

        prefix_id = struct.unpack_from("<H", data, record_start)[0]
        exp_table_id, max_level = struct.unpack_from("<HI", data, data_offset)
        if max_level > _LEVEL_CAPACITY:
            raise ValueError(f"pet exp record {row} max_level exceeds capacity")

        level_exp = struct.unpack_from(f"<{_LEVEL_CAPACITY}Q", data, data_offset + 6)

        populated = level_exp[:max_level]
        for level, required_exp in enumerate(populated, start=1):
            records.append({
                "row": row,
                "exp_table_id": exp_table_id,
                "prefix_exp_table_id": prefix_id,
                "offset_exp_table_id": offset_row.entry_id,
                "key_match": prefix_id == exp_table_id == offset_row.entry_id,
                "max_level": max_level,
                "level": level,
                "required_exp": required_exp,
                "data_offset": data_offset,
                "data_size": data_size,
            })

    return records
