"""Title names, shared by the tables that link a `title.dbss` title.

LOC type 1 holds each title's name under its ID, and its requirement text
under `str_id4` 1.
"""

from __future__ import annotations

from _common.loc import loc_text

LOC_TITLE = 1


def title_name(title_id: int) -> str:
    """English name of a title without its colour tags, or '' when LOC is not loaded or has none."""
    return loc_text(LOC_TITLE, title_id)
