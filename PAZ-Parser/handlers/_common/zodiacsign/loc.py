"""Zodiac sign names and traits in the user's language.

LOC type 7 keys a sign by its zodiac ID: `str_id4` 0 is the name and 1 the
trait list. `zodiacsign.dbss` keeps the Korean of both inline, the fallback
when LOC is not loaded.
"""

from __future__ import annotations

from _common.loc import loc_text

LOC_ZODIAC = 7
_LOC_TRAIT_ID4 = 1


def zodiac_name(zodiac_id: int, korean: str = "") -> str:
    """LOC name of a sign, else its Korean constellation name, else `#<id>`."""
    return loc_text(LOC_ZODIAC, zodiac_id) or korean or f"#{zodiac_id}"


def zodiac_trait(zodiac_id: int, korean: str = "") -> str:
    """LOC trait list of a sign, else its Korean trait text."""
    return loc_text(LOC_ZODIAC, zodiac_id, _LOC_TRAIT_ID4) or korean
