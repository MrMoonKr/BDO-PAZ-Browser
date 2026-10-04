from __future__ import annotations

from _common.binary import u8, u16, u32
from .model import QuestListRecord


_MAGIC = b"PABR"
_HEADER_SIZE = 8
_FIRST_GROUP_HEADER_SIZE = 10
_GROUP_HEADER_SIZE = 23
_ROW_SIZE = 17


def _row_count(data: bytes, offset: int, group: int) -> int:
    if group == 0:
        return u8(data, offset + 7)
    return u16(data, offset + 0x14)


def _group_key(data: bytes, offset: int, group: int) -> int:
    """The group's key, the LOC `str_id1` of its name: a u32 at the start of
    the first header, a u16 at `+0x0D` of the later ones."""
    if group == 0:
        return u32(data, offset)
    return u16(data, offset + 0x0D)


def _header_size(group: int) -> int:
    if group == 0:
        return _FIRST_GROUP_HEADER_SIZE
    return _GROUP_HEADER_SIZE


def parse_quest_list_records(data: bytes) -> list[QuestListRecord]:
    """Read the quest groups of `newquest.bss`, `mainquest.bss`,
    `recommendationquest.bss` or `repetitionquest.bss`, which share one layout."""
    if len(data) < _HEADER_SIZE:
        return []

    if data[:4] != _MAGIC:
        raise ValueError("Quest list has invalid magic.")

    group_count = u32(data, 4)
    offset = _HEADER_SIZE
    records: list[QuestListRecord] = []

    for group in range(group_count):
        header_size = _header_size(group)
        if offset + header_size > len(data):
            break

        count = _row_count(data, offset, group)
        group_key = _group_key(data, offset, group)
        offset += header_size

        for row in range(count):
            if offset + _ROW_SIZE > len(data):
                return records

            quest_chain_id = u16(data, offset + 1)
            quest_id = u16(data, offset + 3)
            records.append({
                "group": group,
                "group_key": group_key,
                "row": row,
                "unknown_00": u8(data, offset),
                "quest_chain_id": quest_chain_id,
                "quest_id": quest_id,
                "packed_quest_id": (quest_id << 16) | quest_chain_id,
                "unknown_05": u32(data, offset + 5),
                "unknown_09": u32(data, offset + 9),
                "unknown_0d": u32(data, offset + 13),
            })
            offset += _ROW_SIZE

    return records
