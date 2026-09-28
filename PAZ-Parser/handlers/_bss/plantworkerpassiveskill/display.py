"""How a passive skill's effect parameters are shown.

Each skill shows three cells: Target (what the skill affects), Effect A (how
much, or how likely for a refund) and Effect B (the refund share; a dash for
every other type). The raw fields mean
different things per effect type (checked against every English description
in the 2026-09-27 client):

- type 0, flat stats: `effect_value_b` picks the stat (0 move speed, 1 work
  speed, 2 luck); `effect_target` 1 to 13 narrows work speed to one work
  category, 0 is generic; `effect_value_a` is the amount
- type 1, full refund: `effect_target` is the chance, `effect_value_a` the
  share of the material refunded; `effect_value_b` always equals it
- type 2, stats per level up: `effect_target` picks the stat with the same
  0/1/2 codes; `effect_value_a` is the amount per level
- type 6, extra work: `effect_target` is the production category,
  `effect_value_a` a plain count

Records keep the raw integers, so sorting and export stay exact.
"""

from __future__ import annotations

from enum import IntEnum
from typing import NamedTuple

from _bss.plantworker.display import LUCK_SCALE, WORK_SPEED_SCALE


class EffectType(IntEnum):
    FLAT_STATS = 0
    FULL_REFUND = 1
    STATS_PER_LEVEL_UP = 2
    EXTRA_WORK = 6


EFFECT_TYPE_LABELS: dict[EffectType, str] = {
    EffectType.FLAT_STATS: "Flat Stats",
    EffectType.FULL_REFUND: "Full Refund",
    EffectType.STATS_PER_LEVEL_UP: "Stats per Level Up",
    EffectType.EXTRA_WORK: "Extra Work",
}


class SkillStat(IntEnum):
    MOVE_SPEED = 0
    WORK_SPEED = 1
    LUCK = 2


STAT_LABELS: dict[SkillStat, str] = {
    SkillStat.MOVE_SPEED: "Move Speed",
    SkillStat.WORK_SPEED: "Work Speed",
    SkillStat.LUCK: "Luck",
}

# Work categories of flat work-speed skills, named as their descriptions name them.
WORK_CATEGORY_LABELS: dict[int, str] = {
    1: "Jeweler",
    2: "Mass Production",
    3: "Weapon/Armor",
    4: "Tool",
    5: "Furniture",
    7: "Costume",
    8: "Refinery/Specialty",
    9: "Cannon/Siege Weapon",
    10: "Ship/Wagon/Horse Gear",
    11: "Node",
    13: "Specialty Node",
}

# Production categories of extra-work skills, named as their descriptions name them.
EXTRA_WORK_LABELS: dict[int, str] = {
    5001: "Weapons",
    5002: "Armor",
    5003: "Life Clothes",
    5004: "Siege Weapons",
    9001: "Produce Packing",
    9002: "Herb Packing",
    9003: "Mushroom Packing",
    9004: "Fish Packing",
    9005: "Timber Packing",
    9006: "Ore Packing",
}

# Move speed bonuses, chances and refund shares are percent × 10,000 (70000 is +7%).
PERCENT_SCALE = 10_000
_GENERIC_TARGET = 0
_EMPTY = "-"


class EffectCells(NamedTuple):
    target: str
    effect_a: str
    effect_b: str


def _number(value: float) -> str:
    return f"{value:g}"


def _percent(raw: int) -> str:
    return f"{_number(raw / PERCENT_SCALE)}%"


def _stat_or_none(code: int) -> SkillStat | None:
    return SkillStat(code) if code in SkillStat._value2member_map_ else None


def _stat_amount(stat: SkillStat | None, raw: int) -> str:
    if stat is None:
        return str(raw)
    if stat is SkillStat.MOVE_SPEED:
        return f"+{_percent(raw)}"
    scale = WORK_SPEED_SCALE if stat is SkillStat.WORK_SPEED else LUCK_SCALE
    return f"+{_number(raw / scale)}"


def _stat_label(stat: SkillStat | None, raw: int) -> str:
    return STAT_LABELS[stat] if stat is not None else str(raw)


def _flat_stats(effect_target: int, value_a: int, value_b: int | None) -> EffectCells:
    selector = value_b or 0
    stat = _stat_or_none(selector)
    target = _stat_label(stat, selector)
    if effect_target != _GENERIC_TARGET:
        category = WORK_CATEGORY_LABELS.get(effect_target, str(effect_target))
        target = f"{category} {target}"
    return EffectCells(target, _stat_amount(stat, value_a), _EMPTY)


def format_effect(
    effect_type: int, effect_target: int, value_a: int, value_b: int | None
) -> EffectCells:
    """The Target, Effect A and Effect B cells for one skill's raw parameters."""
    if effect_type == EffectType.FLAT_STATS:
        return _flat_stats(effect_target, value_a, value_b)
    if effect_type == EffectType.FULL_REFUND:
        # effect_target holds the chance, so there is no target to show. Effect A
        # is the chance, Effect B the share refunded (value_b repeats it).
        return EffectCells(_EMPTY, _percent(effect_target), _percent(value_a))
    if effect_type == EffectType.STATS_PER_LEVEL_UP:
        stat = _stat_or_none(effect_target)
        return EffectCells(_stat_label(stat, effect_target), _stat_amount(stat, value_a), _EMPTY)
    if effect_type == EffectType.EXTRA_WORK:
        target = EXTRA_WORK_LABELS.get(effect_target, str(effect_target))
        return EffectCells(target, f"+{value_a}", _EMPTY)
    return EffectCells(str(effect_target), str(value_a), _EMPTY if value_b is None else str(value_b))


def format_effect_type(effect_type: int) -> str:
    """The effect type's name; the raw number for a type not seen yet."""
    try:
        return EFFECT_TYPE_LABELS[EffectType(effect_type)]
    except ValueError:
        return str(effect_type)
