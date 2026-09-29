"""`--where` conditions over parsed records.

    field=value    equal; numbers compare as numbers (0x hex allowed), text
                   ignores case, true/false/yes/no/1/0 match flags, `none`
                   or an empty value matches an empty cell (None, blank
                   text, an empty list), as the table sort defines it
    field=a..b     number in the inclusive range; `a..` and `..b` leave a side open
    field*=text    text contains `text`, ignoring case; text fields are
                   searched as stored, so `\\n` finds an escaped newline and
                   not a real one

A list value matches when any of its items does, so `buff_ids=48723` finds
every skill that applies that buff. Several conditions must all match.
"""
from __future__ import annotations

import math
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum

from table_sort import is_empty

from .errors import CliError
from .values import display_text, is_number, parse_int, parse_number

_CONDITION_RE = re.compile(r"^(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*(?P<op>\*=|=)(?P<value>.*)$")
_TRUE_WORDS = frozenset({"true", "yes", "1"})
_FALSE_WORDS = frozenset({"false", "no", "0"})
_NONE_WORDS = frozenset({"", "none", "null"})


class Op(Enum):
    EQUALS = "="
    RANGE = ".."
    CONTAINS = "*="


@dataclass(frozen=True)
class Condition:
    field: str
    op: Op
    text: str = ""
    low: int | float | None = None
    high: int | float | None = None

    def matches(self, record: dict) -> bool:
        value = record.get(self.field)
        if self.op is Op.EQUALS and self.text.lower() in _NONE_WORDS:
            # Checked on the whole value: an empty list has no item to test.
            return is_empty(value)
        return _any_item(value, self._matches_scalar)

    def _matches_scalar(self, value: object) -> bool:
        if self.op is Op.CONTAINS:
            return _contains(value, self.text)
        if self.op is Op.RANGE:
            return _in_range(value, self.low, self.high)
        return _equals(value, self.text)


def parse_condition(text: str) -> Condition:
    """Parse one `--where` argument. Raises CliError with the accepted forms."""
    match = _CONDITION_RE.match(text.strip())
    if match is None:
        raise CliError(f"cannot read --where '{text}', use field=value, field=a..b or field*=text.")

    field, op, value = match["field"], match["op"], match["value"].strip()
    if op == Op.CONTAINS.value:
        return Condition(field, Op.CONTAINS, text=value)

    bounds = _parse_range(value)
    if bounds is not None:
        low, high = bounds
        return Condition(field, Op.RANGE, text=value, low=low, high=high)
    return Condition(field, Op.EQUALS, text=value)


def check_fields(conditions: Sequence[Condition], fields: Sequence[str]) -> None:
    """Fail on a condition naming a field the records do not have."""
    known = set(fields)
    unknown = sorted({c.field for c in conditions} - known)
    if unknown:
        raise CliError(
            f"unknown field(s) in --where: {', '.join(unknown)}. Fields: {', '.join(fields)}"
        )


def filter_records(records: list[dict], conditions: Sequence[Condition]) -> list[dict]:
    return [r for r in records if all(c.matches(r) for c in conditions)]


def _parse_range(value: str) -> tuple[int | float | None, int | float | None] | None:
    if ".." not in value:
        return None
    low_text, _, high_text = value.partition("..")
    try:
        low = parse_number(low_text) if low_text.strip() else None
        high = parse_number(high_text) if high_text.strip() else None
    except ValueError:
        raise CliError(f"range '{value}': the bounds must be numbers, e.g. 10..20, 10.. or ..20.") from None
    if low is None and high is None:
        raise CliError("a range needs at least one bound, e.g. 10..20, 10.. or ..20.")
    return low, high


def _any_item(value: object, test: Callable[[object], bool]) -> bool:
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_any_item(item, test) for item in value)
    return test(value)


def _in_range(value: object, low: int | float | None, high: int | float | None) -> bool:
    if not is_number(value):
        return False
    number = float(value)  # type: ignore[arg-type]  # is_number checked it
    return (low is None or number >= low) and (high is None or number <= high)


def _as_text(value: object) -> str:
    """Strings as stored; display_text would turn a newline into a visible escape."""
    return value if isinstance(value, str) else display_text(value)


def _contains(value: object, text: str) -> bool:
    return value is not None and text.casefold() in _as_text(value).casefold()


def _equals(value: object, text: str) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        word = text.lower()
        return (value and word in _TRUE_WORDS) or (not value and word in _FALSE_WORDS)
    if isinstance(value, int):
        try:
            return value == parse_int(text)
        except ValueError:
            return _float_equals(value, text)
    if isinstance(value, float):
        return _float_equals(value, text)
    return _as_text(value).casefold() == text.casefold()


def _float_equals(value: float, text: str) -> bool:
    try:
        return math.isclose(value, float(text), rel_tol=1e-9, abs_tol=1e-12)
    except ValueError:
        return False
