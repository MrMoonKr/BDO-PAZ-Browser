"""`plantzone.dbss`: worker production zones, located through `plantzoneoffset.dbss`.

    u32 record_id | u32 | u32 | u16 | u8 unknown_0e | u16 | u16 | u32
    | u16 production_key | u16 unknown_19 | u32 species_count
    | u8[species_count] worker_species

Full layout in docs/file-formats/plantzone_dbss.md.
"""

from __future__ import annotations

import struct

_OFFSET_ROW_SIZE = 12
_OFFSET_HEADER_SIZE = 4

# Record field offsets; the last four are unaligned.
_UNKNOWN_0E = 0x0E
_PRODUCTION_KEY = 0x17
_UNKNOWN_19 = 0x19
_SPECIES_COUNT = 0x1B
_SPECIES = 0x1F

# Worker species byte (plantworker.bss +0x38F), named after the workers that
# carry each value; the client enum was not found.
WORKER_SPECIES_NAMES: tuple[str, ...] = (
    "Goblin", "Human", "Giant", "Papu", "Fadus", "Dwarf", "Dokkebi", "Dolswe", "Shellfolk",
)


def parse_offset_records(data: bytes) -> list[dict]:
    if len(data) < _OFFSET_HEADER_SIZE:
        return []

    count = struct.unpack_from("<I", data, 0)[0]
    records: list[dict] = []

    for i in range(count):
        pos = _OFFSET_HEADER_SIZE + i * _OFFSET_ROW_SIZE
        if pos + _OFFSET_ROW_SIZE > len(data):
            break
        record_id, _zero, data_offset, data_size = struct.unpack_from("<HHII", data, pos)
        records.append({
            "record_id": record_id,
            "data_offset": data_offset,
            "data_size": data_size,
        })

    return records


def parse_plantzone_records(data: bytes, offset_data: bytes) -> list[dict]:
    """One zone per offset row, in offset-file order.

    Raises ValueError when a row points past the file or its species list does
    not end exactly at the row's size: every later field would then be misread.
    """
    records: list[dict] = []

    for off in parse_offset_records(offset_data):
        start = off["data_offset"]
        size = off["data_size"]
        record_id = off["record_id"]
        if start + size > len(data) or size < _SPECIES:
            raise ValueError(f"plantzone record {record_id} runs past the end of plantzone.dbss")

        payload = data[start : start + size]
        species_count = struct.unpack_from("<I", payload, _SPECIES_COUNT)[0]
        if _SPECIES + species_count != size:
            raise ValueError(f"plantzone record {record_id} lists {species_count} species in {size} bytes")

        records.append({
            "record_id": struct.unpack_from("<I", payload, 0x00)[0],
            "unknown_0e": payload[_UNKNOWN_0E],
            "production_key": struct.unpack_from("<H", payload, _PRODUCTION_KEY)[0],
            "unknown_19": struct.unpack_from("<H", payload, _UNKNOWN_19)[0],
            "worker_species": list(payload[_SPECIES:]),
            "data_size": size,
        })

    return records
