from __future__ import annotations

from _common.binary import u8, u16, u32


_MAGIC = b"PABR"
_HEADER_SIZE = 4
_SECTION1_COUNT = 43
_SECTION1_RECORD_SIZE = 12
_NULL_BLOCK_COUNT = 15
_NULL_BLOCK_RECORD_SIZE = 16
_SECTION2_RECORD_SIZE = 16
# [u32 0][u32 data_end][u32 0], the same trailer as fairyequipskill.bss.
_TRAILER_SIZE = 12
_NULL_EQUIP_SKILL_ID = 200


def _section1_offset() -> int:
    return _HEADER_SIZE


def _null_block_offset() -> int:
    return _section1_offset() + _SECTION1_COUNT * _SECTION1_RECORD_SIZE


def _section2_offset() -> int:
    return _null_block_offset() + _NULL_BLOCK_COUNT * _NULL_BLOCK_RECORD_SIZE


def _require_size(data: bytes, minimum_size: int) -> None:
    if len(data) < minimum_size:
        raise ValueError(
            f"petequipskill.bss is truncated: expected at least {minimum_size} bytes"
        )


def _parse_section1(data: bytes) -> list[dict]:
    records: list[dict] = []

    for slot in range(_SECTION1_COUNT):
        pos = _section1_offset() + slot * _SECTION1_RECORD_SIZE
        records.append({
            "slot": slot,
            "section": "S1",
            "equip_skill_id": u32(data, pos),
            "skill_type": u32(data, pos + 0x04),
            "unknown_08": u8(data, pos + 0x08),
            "padding": u8(data, pos + 0x09),
            "loc_id": u16(data, pos + 0x0A),
            "unknown_0c": None,
            "unknown_10": None,
        })

    return records


def _parse_section2(data: bytes) -> list[dict]:
    records: list[dict] = []
    pos = _section2_offset()
    end = len(data) - _TRAILER_SIZE
    slot = 0

    while pos + _SECTION2_RECORD_SIZE <= end:
        equip_skill_id = u32(data, pos)
        skill_type = u32(data, pos + 0x04)
        unknown_08 = u8(data, pos + 0x08)
        padding = u8(data, pos + 0x09)
        loc_id = u16(data, pos + 0x0A)
        # 0 or 1; each record with 1 carries one more u32 after the 16 bytes.
        unknown_0c = u32(data, pos + 0x0C)
        pos += _SECTION2_RECORD_SIZE

        if equip_skill_id == _NULL_EQUIP_SKILL_ID:
            slot += 1
            continue

        unknown_10 = None
        if unknown_0c == 1 and pos + 4 <= end:
            unknown_10 = u32(data, pos)
            pos += 4

        records.append({
            "slot": slot,
            "section": "S2",
            "equip_skill_id": equip_skill_id,
            "skill_type": skill_type,
            "unknown_08": unknown_08,
            "padding": padding,
            "loc_id": loc_id,
            "unknown_0c": unknown_0c,
            "unknown_10": unknown_10,
        })
        slot += 1

    return records


def parse_petequipskill_records(data: bytes) -> list[dict]:
    if len(data) < _HEADER_SIZE:
        return []

    if data[:4] != _MAGIC:
        raise ValueError("petequipskill.bss has invalid magic.")

    _require_size(data, _section2_offset())

    return _parse_section1(data) + _parse_section2(data)
