"""Skill keys and skill names shared by the skill tables.

Every table in the skill cluster (`skill.dbss`, `skilltype.dbss`,
`skillgroup.bss`, `ui_skillgroup_*.bss`) keys a skill rank by

    skill_key = skill_no << 16 | level

and LOC type 10 names a skill by its number alone, so every rank of one skill
shares a name. See docs/file-formats/skill_dbss.md.
"""

from __future__ import annotations

from _common.loc import loc_text
from _common.lookup_index import IndexKind, lookup

LOC_SKILL_NAME = 10

_LEVEL_MASK = 0xFFFF


def split_skill_key(skill_key: int) -> tuple[int, int]:
    """`(skill_no, level)` of a skill key."""
    return skill_key >> 16, skill_key & _LEVEL_MASK


def skill_name(skill_no: int) -> str:
    """LOC type 10 name of a skill, then its Korean `skilltype.dbss` name, else ''.

    The Korean names come from the `SKILL_NAME_KR` lookup index, so a table
    needs no `skilltype.dbss` companion for them.
    """
    name = loc_text(LOC_SKILL_NAME, skill_no)
    if name:
        return name
    korean = lookup(IndexKind.SKILL_NAME_KR, skill_no)
    return korean if isinstance(korean, str) else ""
