from __future__ import annotations

from typing import TypedDict


class NewQuestRecord(TypedDict):
    group: int
    group_key: int
    row: int
    unknown_00: int
    quest_chain_id: int
    quest_id: int
    packed_quest_id: int
    unknown_05: int
    unknown_09: int
    unknown_0d: int
