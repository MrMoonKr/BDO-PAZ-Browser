"""What each confirmed effect type's parameters mean, one entry per type.

Every entry drives both the Effect text and the labels of the Param columns,
so a type is described once. The evidence for each type is in
docs/file-formats/buff_dbss.md (Enum Values and Effect text).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from _common.character import character_name
from _common.knowledge import knowledge_name
from _common.quest.quest import quest_title
from .units import FLAT, PERCENT, SECONDS, WEIGHT, Unit


@dataclass(frozen=True)
class EffectLine:
    """One effect a buff of a type can read as.

    The line applies when every parameter in `when` (parameter number to
    value) holds that value and the amount in `value_param` is not zero.
    `kind_labels` names those parameters for the Param columns, and
    `value_label` names the amount where nothing else tells what it is.
    """

    label: str
    value_param: int
    unit: Unit = FLAT
    when: Mapping[int, int] = field(default_factory=dict)
    kind_labels: Mapping[int, str] = field(default_factory=dict)
    value_label: str = ""
    # False for amounts the game prints without a sign: `Recover 10 Energy`.
    is_signed: bool = True
    template: str = "{label} {amount}"


def recovery(label: str, value_param: int) -> EffectLine:
    """A one-off amount: `Recover 10 Energy`."""
    return EffectLine(label, value_param, is_signed=False, template="Recover {amount} {label}")


def kinds(
    kind_param: int,
    label: str,
    names: Mapping[int, str],
    value_param: int,
    unit: Unit = FLAT,
) -> tuple[EffectLine, ...]:
    """One line per value of `kind_param`; `label` may hold `{kind}`."""
    return tuple(
        EffectLine(
            label.format(kind=name),
            value_param,
            unit,
            when={kind_param: kind},
            kind_labels={kind_param: name},
        )
        for kind, name in names.items()
    )


@dataclass(frozen=True)
class NamedEffect:
    """An effect whose parameters are the key of something LOC names.

    `name_of` receives the values of `key_params`; without a name the key is
    shown as `244/1`.
    """

    template: str
    name_of: Callable[..., str]
    key_params: tuple[int, ...] = (1,)


@dataclass(frozen=True)
class FixedDamage:
    """`Retaliate 15 Fixed Damage when struck`."""

    verb: str
    trigger: str


@dataclass(frozen=True)
class OverTimeEffect:
    """HP or MP/WP/SP: `param_1` per tick (`tick_ms`), or per trigger.

    `recover_on` words a positive amount by `condition_type`, and
    `fixed_damage_on` a negative one; other conditions yield no text.
    `damage_kinds` names ticking damage by the buff's icon file, for the
    icons whose English text agrees.
    """

    resource: str
    recover_on: Mapping[int, str] = field(default_factory=dict)
    fixed_damage_on: Mapping[int, FixedDamage] = field(default_factory=dict)
    damage_kinds: Mapping[str, str] = field(default_factory=dict)


_LIFE_SKILLS = {
    0: "Gathering",
    1: "Fishing",
    2: "Hunting",
    3: "Cooking",
    4: "Alchemy",
    5: "Processing",
    6: "Training",
    7: "Trading",
    8: "Farming",
    9: "Sailing",
    11: "Barter",
}

# Type 149 `param_2` by life skill, the same on every buff with text. The
# [Life Skill Season] buffs pair Gathering and Processing with 2 to 7 for
# single tools (`Processing_Hoe Mastery`); those stay unlabelled.
_MASTERY_PARAM_2 = {0: 0, 1: 0, 2: 1, 3: 1, 4: 1, 5: 0, 6: 1, 9: 1}
# Type 149 `param_1` for every life skill at once.
_ALL_LIFE_SKILLS = 15

_RESISTANCES = {
    0: "Knockback/Floating",
    1: "Knockdown/Bound",
    2: "Grapple",
    3: "Stun/Stiffness/Freezing",
    8: "All",
}

EFFECT_LINES: dict[int, tuple[EffectLine, ...]] = {
    2: (EffectLine("Max HP", 1),),
    3: (EffectLine("HP Recovery", 1),),
    5: (EffectLine("Max MP/WP/SP", 1),),
    6: (EffectLine("MP/WP/SP Recovery", 1),),
    8: (EffectLine("Max Stamina", 1),),
    9: (EffectLine("Movement Speed", 1, PERCENT),),
    10: (EffectLine("Attack Speed", 1, PERCENT),),
    11: (EffectLine("Casting Speed", 1, PERCENT),),
    25: kinds(2, "{kind} EXP", {0: "Combat", 1: "Skill", 2: "Life"}, 1, PERCENT),
    29: (EffectLine("Weight Limit", 1, WEIGHT),),
    30: (EffectLine("Critical Hit Rate", 1, PERCENT),),
    # param_1 3 is all targets. bdo-data-extractor reads 0 to 2 as melee,
    # ranged and magic; no buff with those has English text, so no label.
    39: kinds(1, "All AP", {3: "All"}, 2),
    40: kinds(1, "All Accuracy", {3: "All"}, 2),
    41: kinds(1, "All Evasion", {3: "All"}, 2),
    43: kinds(1, "All Damage Reduction", {3: "All"}, 2),
    # Summon, monster, siege and cannon damage as a share of attack; player
    # skills do not use it. param_1 may be the attack type (2 on magic).
    45: (EffectLine("Attack Damage", 4, PERCENT, is_signed=False),),
    # Kind 5 is unused ("Not in Use"); kind 6 mixes hunting effects whose
    # amounts do not follow param_2, so both stay unlabelled.
    46: kinds(
        1,
        "Extra AP Against {kind}",
        {
            0: "Humans",
            1: "Demihumans",
            2: "Beasts",
            3: "Kamasylvian Monsters",
            4: "Edanian Monsters",
        },
        2,
    ),
    # Kinds 3 and 5 are stun and stiffness in Korean but share one English
    # label; kind 6 (bound) reads "Not in Use" and stays unlabelled.
    49: kinds(
        1,
        "{kind} Resistance",
        {**_RESISTANCES, 5: "Stun/Stiffness/Freezing", 7: "Fear"},
        2,
        PERCENT,
    ),
    50: (EffectLine("Mount EXP", 1, PERCENT),),
    57: (EffectLine("Item Drop Rate", 1, PERCENT),),
    63: (recovery("Worker Stamina", 1),),
    67: kinds(
        1,
        "{kind}",
        {
            0: "Movement Speed",
            1: "Attack Speed",
            2: "Casting Speed",
            3: "Critical Hit",
            4: "Luck",
            5: "Fishing Speed",
            6: "Gathering Speed",
        },
        2,
    ),
    79: (recovery("Energy", 1),),
    80: kinds(1, "{kind} EXP", _LIFE_SKILLS, 2),
    89: kinds(1, "{kind} EXP", {0: "Breath", 1: "Strength", 2: "Health"}, 2),
    90: (EffectLine("Death Penalty Resistance", 1, PERCENT),),
    93: kinds(
        1,
        "{kind} Extra Damage",
        {
            0: "All Special Attack",
            1: "Back Attack",
            2: "Down Attack",
            3: "Air Attack",
            4: "Critical Hit",
            5: "Speed Attack",
            6: "Counter Attack",
        },
        2,
        PERCENT,
    ),
    94: (EffectLine("Max Energy", 1),),
    95: (EffectLine("Underwater Breathing", 1, SECONDS),),
    105: kinds(1, "Ignore {kind} Resistance", _RESISTANCES, 2, PERCENT),
    108: (EffectLine("Knowledge Gain Chance", 1, PERCENT),),
    109: (EffectLine("Higher Grade Knowledge Gain Chance", 1, PERCENT),),
    # param_1 picks a rate (0) or a flat amount (2).
    120: (
        *kinds(1, "Monster Damage Reduction Rate", {0: "Rate"}, 2, PERCENT),
        *kinds(1, "Monster Damage Reduction", {2: "Flat"}, 2),
    ),
    128: kinds(1, "{kind} Resistance", {0: "Heatstroke", 1: "Hypothermia"}, 2, PERCENT),
    # One amount per target; no buff sets both.
    136: (
        EffectLine("Extra AP Against Monsters", 1, value_label="Monster AP"),
        EffectLine("Extra AP Against Adventurers", 2, value_label="Adventurer AP"),
    ),
    149: (
        *(
            EffectLine(
                f"{_LIFE_SKILLS[skill]} Mastery",
                3,
                when={1: skill, 2: param_2},
                kind_labels={1: _LIFE_SKILLS[skill]},
            )
            for skill, param_2 in _MASTERY_PARAM_2.items()
        ),
        EffectLine(
            "Life Skill Mastery",
            3,
            when={1: _ALL_LIFE_SKILLS, 2: 0},
            kind_labels={1: "All"},
        ),
    ),
}

NAMED_EFFECTS: dict[int, NamedEffect] = {
    # The summoned character. Siege objects and placed objects are characters too.
    18: NamedEffect("Summon {name}", character_name),
    # Hidden buffs that items used on pickup apply to unlock a knowledge entry.
    38: NamedEffect("Learn Knowledge: {name}", knowledge_name),
    # Accepts quest `param_2` of chain `param_1`: Cartian Spell's "[Co-op]
    # Eliminating the Threats to Mediah will automatically be accepted".
    69: NamedEffect("Accept Quest: {name}", quest_title, key_params=(1, 2)),
}

OVER_TIME_EFFECTS: dict[int, OverTimeEffect] = {
    1: OverTimeEffect(
        "HP",
        recover_on={1: "on Hits", 3: "when struck", 9: "on Critical Hits"},
        fixed_damage_on={
            4: FixedDamage("Retaliate", "when struck"),
            6: FixedDamage("Deal", "on Back Attack Hits"),
            10: FixedDamage("Deal", "on Critical Hits"),
        },
        # dot_bleeding.dds is left out: 201 of its texts say "burn".
        damage_kinds={
            "dot_poison.dds": "poison",
            "dot_burns.dds": "burn",
            "dot_pains.dds": "pain",
        },
    ),
    4: OverTimeEffect("MP/WP/SP", recover_on={1: "on Hits", 8: "when struck"}),
}
