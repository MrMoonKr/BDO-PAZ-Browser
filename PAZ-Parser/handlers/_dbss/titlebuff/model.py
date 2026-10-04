from __future__ import annotations

from typing import TypedDict


class TitleBuffRecord(TypedDict):
    tier_id: int
    offset: int
    required_titles: int
    unknown_08: int
    unknown_09: int
    unknown_0a: int
    label_kr: str
    effect_kr: str
