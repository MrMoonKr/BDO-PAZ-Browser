"""Cell text for sailor stats and weight, as the Manage Sailors window shows them."""

from __future__ import annotations

from pathlib import Path

from _common.lang import load_handler_strings
from .parser import STAT_FIELDS

_LANG_DIR = Path(__file__).parent / "lang"
# Stored stats are percent x 10,000; the window shows them with one decimal.
_STAT_SCALE = 10_000
# Stored weight is in 1/10,000 LT.
_WEIGHT_SCALE = 10_000


def stat_text(value: int) -> str:
    """`16000` -> `1.6%`, as `string.format("%.1f", value * 0.0001)` in the sailor Lua."""
    return f"{value / _STAT_SCALE:.1f}%"


def stat_labels(lang: str) -> dict[int, str]:
    """Ability type -> the window's stat label in `lang`; shared with `employeeexp.bss`."""
    columns = load_handler_strings(lang, _LANG_DIR)["columns"]
    return {kind: columns[field] for kind, field in STAT_FIELDS.items()}


def weight_text(value: int) -> str:
    """`2500000` -> `250 LT`; a fraction of an LT is kept (`12.5 LT`)."""
    return f"{value / _WEIGHT_SCALE:,g} LT"
