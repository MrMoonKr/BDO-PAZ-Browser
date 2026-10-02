"""Display-only record fields.

A record key starting with `_` holds data for rendering only, such as LOC text
with its game colour tags (`_description_pa` next to the plain
`description`). Search, sort and CSV export skip it and use the plain field
instead; the CLI record table and JSON keep it, to show the tags. See
"Display-Only Fields" in docs/handler.md.
"""
from __future__ import annotations

DISPLAY_FIELD_PREFIX = "_"


def is_display_field(key: str) -> bool:
    """True for a key that is for rendering only."""
    return key.startswith(DISPLAY_FIELD_PREFIX)


def record_matches(record: dict, query: str) -> bool:
    """True when `query` (lowercase) is in a value of `record` that is not display-only."""
    return any(query in str(value).lower() for key, value in record.items() if not is_display_field(key))


def data_fields(record: dict) -> list[str]:
    """The keys of `record` that are not display-only, in record order."""
    return [key for key in record if not is_display_field(key)]
