"""Knowledge entry names, shared by the tables that link a knowledge entry.

LOC type 34 holds each entry's name under its ID, and other sub-fields of the
same ID (the "how to obtain" text, see `_dbss/mentalcard/handler.py`).
"""

from __future__ import annotations

from _common.loc import loc_text

LOC_KNOWLEDGE = 34


def knowledge_name(knowledge_id: int) -> str:
    """English name of a knowledge entry, or '' when LOC is not loaded or has none."""
    return loc_text(LOC_KNOWLEDGE, knowledge_id)
