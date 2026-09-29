"""Record values as the CLI reads and prints them."""
from __future__ import annotations

from collections.abc import Mapping

_HEX_PREFIX = "0x"
_EMPTY = "-"


def parse_int(text: str) -> int:
    """A decimal or 0x hex integer. Raises ValueError."""
    stripped = text.strip()
    body = stripped.lstrip("+-")
    if body.lower().startswith(_HEX_PREFIX):
        return int(stripped, 16)
    return int(stripped, 10)


def parse_number(text: str) -> int | float:
    """An integer (decimal or 0x hex) or a float. Raises ValueError."""
    try:
        return parse_int(text)
    except ValueError:
        return float(text)


def is_number(value: object) -> bool:
    """True for ints and floats; bools are flags, not numbers."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def display_text(value: object) -> str:
    """One-line text for a table cell: lists joined, None as a dash."""
    if value is None:
        return _EMPTY
    if isinstance(value, (bytes, bytearray)):
        return value.hex(" ")
    if isinstance(value, Mapping):
        return ", ".join(f"{k}={display_text(v)}" for k, v in value.items())
    if isinstance(value, (list, tuple, set, frozenset)):
        return ", ".join(display_text(item) for item in value)
    return str(value).replace("\r", "").replace("\n", "\\n").replace("\t", " ")
