"""How stored buff amounts are scaled and written."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Unit:
    """How a stored amount is scaled and suffixed for display."""

    divisor: int = 1
    suffix: str = ""

    @property
    def is_scaled(self) -> bool:
        """True when the stored number differs from what the game shows."""
        return self.divisor != 1 or bool(self.suffix)


FLAT = Unit()
# Percentages are stored per million: 25000 is 2.5%.
PERCENT = Unit(10_000, "%")
# Weight is stored in ten-thousandths of an LT: 1000000 is 100 LT.
WEIGHT = Unit(10_000, " LT")
# Durations are stored in milliseconds.
SECONDS = Unit(1_000, " sec")

_MAX_DECIMALS = 4


def format_amount(value: int, unit: Unit, *, signed: bool) -> str:
    """`+150`, `-6`, `+2,560,350`, `+2.5%`, `+100 LT`, or `10` unsigned."""
    sign = "+" if signed else ""
    if unit.divisor == 1:
        number = f"{value:{sign},}"
    else:
        scaled = f"{value / unit.divisor:{sign},.{_MAX_DECIMALS}f}"
        number = scaled.rstrip("0").rstrip(".")
    return number + unit.suffix


def seconds_text(milliseconds: int) -> str:
    """`10`, `1.5`."""
    return f"{milliseconds / 1_000:.3f}".rstrip("0").rstrip(".")
