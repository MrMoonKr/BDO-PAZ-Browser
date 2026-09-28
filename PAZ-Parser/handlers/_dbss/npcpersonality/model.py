from __future__ import annotations

from typing import TypedDict


class NpcPersonalityRecord(TypedDict):
    row: int
    personality_id: int
    group_a_id: int
    unknown_04: int
    group_b_id: int
    unknown_08: int
    group_c_id: int
    unknown_0c: int
    interest_min: float
    interest_max: float
    favor_min: float
    favor_max: float
    personality_type: int


class NpcPersonalityOffsetRecord(TypedDict):
    row: int
    personality_id: int
    data_offset: int
    data_size: int
