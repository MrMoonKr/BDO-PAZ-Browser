"""Display fields for `employeeexp.bss` rows, kept apart from the handler so tests can import them."""

from __future__ import annotations

from collections.abc import Iterable, Mapping


def growth_text(growth_dice: list[str], labels: Mapping[int, str]) -> str:
    """The abilities a level-up rolls, as `Endurance: 1D2, Wits: 1D2+1`; empty when it rolls none.

    The slot in `growth_dice` is the ability type of `employeestaticstatus.bss`;
    `labels` names them, and a type without a label shows its number.
    """
    return ", ".join(
        f"{labels.get(ability, ability)}: {dice}"
        for ability, dice in enumerate(growth_dice)
        if dice
    )


def top_levels(records: Iterable[dict]) -> dict[int, int]:
    """The highest level each sailor has a row for."""
    top: dict[int, int] = {}
    for record in records:
        key = record["employee_key"]
        top[key] = max(top.get(key, 0), record["level"])
    return top
