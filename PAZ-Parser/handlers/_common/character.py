"""Character names, shared by the tables that link a character.

LOC type 6 holds the name plate of every character key: monsters, NPCs,
summons, siege objects and placed furniture. `str_id4` 0 is the name and 1
the title above it (`<Storage Keeper>`), `<null>` when the character has none.
"""

from __future__ import annotations

from _common.loc import LOC_NULL, loc_text

LOC_CHARACTER_NAME = 6
_LOC_TITLE_ID4 = 1


def character_name(character_id: int) -> str:
    """Name of a character in the loaded LOC language, or '' when LOC is not loaded or has none."""
    return loc_text(LOC_CHARACTER_NAME, character_id)


def character_title(character_id: int) -> str:
    """Title of a character in the loaded LOC language, or '' when it has none."""
    title = loc_text(LOC_CHARACTER_NAME, character_id, _LOC_TITLE_ID4)
    return "" if title == LOC_NULL else title
