"""Effect text of a buff, read from its parameters.

The parameters are the applied value; the name and the description can both
be stale (see docs/file-formats/buff_dbss.md). Only the effect types whose
parameters are confirmed against the English LOC type 5 text get a text, in
the game's own wording (`Life EXP +15%`); every other type yields ''.

Kept out of `handler.py` so the tests can import it (see "Unit Tests" in
docs/handler.md).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

# Percentages are stored per million: 25000 is 2.5%.
_PER_MILLION_TO_PERCENT = 10_000


@dataclass(frozen=True)
class _EffectFormat:
    """How one effect type reads.

    `labels` is the label itself, or the labels by the value of the
    `kind_param` parameter; a kind missing there yields no text.
    """

    labels: str | Mapping[int, str]
    value_param: int
    kind_param: int | None = None
    is_percent: bool = False


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

_EFFECT_FORMATS: dict[int, _EffectFormat] = {
    2: _EffectFormat("Max HP", value_param=1),
    3: _EffectFormat("HP Recovery", value_param=1),
    5: _EffectFormat("Max MP/WP/SP", value_param=1),
    6: _EffectFormat("MP/WP/SP Recovery", value_param=1),
    8: _EffectFormat("Max Stamina", value_param=1),
    9: _EffectFormat("Movement Speed", value_param=1, is_percent=True),
    10: _EffectFormat("Attack Speed", value_param=1, is_percent=True),
    11: _EffectFormat("Casting Speed", value_param=1, is_percent=True),
    25: _EffectFormat(
        {0: "Combat EXP", 1: "Skill EXP", 2: "Life EXP"},
        value_param=1,
        kind_param=2,
        is_percent=True,
    ),
    30: _EffectFormat("Critical Hit Rate", value_param=1, is_percent=True),
    # param_1 3 is all targets. bdo-data-extractor reads 0 to 2 as melee,
    # ranged and magic; no buff with those has English text, so no label.
    39: _EffectFormat({3: "All AP"}, value_param=2, kind_param=1),
    40: _EffectFormat({3: "All Accuracy"}, value_param=2, kind_param=1),
    41: _EffectFormat({3: "All Evasion"}, value_param=2, kind_param=1),
    43: _EffectFormat({3: "All Damage Reduction"}, value_param=2, kind_param=1),
    80: _EffectFormat(
        {kind: f"{skill} EXP" for kind, skill in _LIFE_SKILLS.items()},
        value_param=2,
        kind_param=1,
    ),
    93: _EffectFormat(
        {
            0: "All Special Attack Extra Damage",
            1: "Back Attack Extra Damage",
            2: "Down Attack Extra Damage",
            3: "Air Attack Extra Damage",
            4: "Critical Hit Extra Damage",
            5: "Speed Attack Extra Damage",
            6: "Counter Attack Extra Damage",
        },
        value_param=2,
        kind_param=1,
        is_percent=True,
    ),
    105: _EffectFormat(
        {
            0: "Ignore Knockback/Floating Resistance",
            1: "Ignore Knockdown/Bound Resistance",
            2: "Ignore Grapple Resistance",
            3: "Ignore Stun/Stiffness/Freezing Resistance",
            8: "Ignore All Resistance",
        },
        value_param=2,
        kind_param=1,
        is_percent=True,
    ),
    128: _EffectFormat(
        {0: "Heatstroke Resistance", 1: "Hypothermia Resistance"},
        value_param=2,
        kind_param=1,
        is_percent=True,
    ),
}


def _signed_amount(value: int, is_percent: bool) -> str:
    """`+150`, `-6`, `+2,560,350` or `+2.5%`."""
    if not is_percent:
        return f"{value:+,}"
    percent = value / _PER_MILLION_TO_PERCENT
    return f"{percent:+,.4f}".rstrip("0").rstrip(".") + "%"


def _label(effect: _EffectFormat, params: Sequence[int]) -> str:
    if isinstance(effect.labels, str):
        return effect.labels
    if effect.kind_param is None:
        return ""
    return effect.labels.get(params[effect.kind_param - 1], "")


def effect_text(effect_type: int, params: Sequence[int]) -> str:
    """`All AP +8` for a confirmed effect type, else ''.

    `params` holds `param_1` onwards, so `params[0]` is `param_1`.
    """
    effect = _EFFECT_FORMATS.get(effect_type)
    if effect is None:
        return ""
    label = _label(effect, params)
    if not label:
        return ""
    return f"{label} {_signed_amount(params[effect.value_param - 1], effect.is_percent)}"
