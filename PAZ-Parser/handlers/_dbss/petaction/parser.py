from __future__ import annotations

import struct
from pathlib import PureWindowsPath

from _common.prefixed_string import read_prefixed_at


_OFFSET_HEADER_SIZE = 4
_OFFSET_RECORD_SIZE = 12
_NAME_PREFIX_OFFSET = 0x10
_TRAILER_SIZE = 12
_MAGIC = 0xDEBA1DCD


def parse_petactionoffset_records(data: bytes) -> list[dict]:
    if len(data) < _OFFSET_HEADER_SIZE:
        return []

    (count,) = struct.unpack_from("<I", data, 0)
    records: list[dict] = []

    for index in range(count):
        pos = _OFFSET_HEADER_SIZE + index * _OFFSET_RECORD_SIZE
        if pos + _OFFSET_RECORD_SIZE > len(data):
            break

        action_id, record_offset, record_size = struct.unpack_from("<III", data, pos)
        records.append({
            "action_id": action_id,
            "record_offset": record_offset,
            "record_size": record_size,
        })

    return records


def _derive_action_name(icon_path: str) -> str:
    stem = PureWindowsPath(icon_path.replace("/", "\\")).stem
    parts = stem.split("_")
    if len(parts) >= 3 and parts[0].lower() == "action":
        return parts[-1]
    return stem


def _parse_petaction_payload(row: int, offset_record: dict, block: bytes) -> dict:
    if len(block) < _NAME_PREFIX_OFFSET + _TRAILER_SIZE:
        raise ValueError(f"pet action record {row} is too small")

    action_id, reserved_04, reserved_08, magic = struct.unpack_from("<IIII", block, 0x00)
    if magic != _MAGIC:
        raise ValueError(f"pet action record {row} has unexpected magic 0x{magic:08X}")

    # Two u64-length UTF-16 strings follow: the Korean action name, then the icon path.
    name_kr, path_prefix = read_prefixed_at(block, _NAME_PREFIX_OFFSET, len(block), wide=True)
    icon_path, path_end = read_prefixed_at(block, path_prefix, len(block), wide=True)
    trailer = block[path_end:]
    if len(trailer) != _TRAILER_SIZE:
        raise ValueError(
            f"pet action record {row} has {len(trailer)} bytes after the icon path, expected {_TRAILER_SIZE}"
        )

    return {
        "row": row,
        "action_id": action_id,
        "action_name": _derive_action_name(icon_path),
        "name_kr": name_kr,
        "icon_path": icon_path,
        "magic": magic,
        "magic_hex": f"0x{magic:08X}",
        "record_offset": offset_record["record_offset"],
        "record_size": offset_record["record_size"],
        "reserved_04": reserved_04,
        "reserved_08": reserved_08,
        "trailing_zeroes": trailer == b"\x00" * _TRAILER_SIZE,
        "action_id_match": action_id == offset_record["action_id"],
    }


def parse_petaction_records(data: bytes, offset_data: bytes) -> list[dict]:
    records: list[dict] = []

    for row, offset_record in enumerate(parse_petactionoffset_records(offset_data)):
        start = offset_record["record_offset"]
        size = offset_record["record_size"]
        if start + size > len(data):
            raise ValueError(f"pet action record {row} exceeds file size")

        block = data[start:start + size]
        records.append(_parse_petaction_payload(row, offset_record, block))

    return sorted(records, key=lambda record: record["action_id"])
