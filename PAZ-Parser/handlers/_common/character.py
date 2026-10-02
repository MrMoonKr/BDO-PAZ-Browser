"""Character names, shared by the tables that link a character.

LOC type 6 holds the name plate of every character key: monsters, NPCs,
summons, siege objects and placed furniture.
"""

from __future__ import annotations

from _common.loc import loc_text

LOC_CHARACTER_NAME = 6


def character_name(character_id: int) -> str:
    """English name of a character, or '' when LOC is not loaded or has none."""
    return loc_text(LOC_CHARACTER_NAME, character_id)
