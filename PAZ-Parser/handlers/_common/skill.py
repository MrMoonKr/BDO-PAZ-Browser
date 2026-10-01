"""Skill keys and skill names shared by the skill tables.

Every table in the skill cluster (`skill.dbss`, `skilltype.dbss`,
`skillgroup.bss`, `ui_skillgroup_*.bss`) keys a skill rank by

    skill_key = skill_no << 16 | level

and LOC type 10 names a skill by its number alone, so every rank of one skill
shares a name. See docs/file-formats/skill_dbss.md.
"""

from __future__ import annotations

from collections.abc import Iterable

from _common.loc import LOC_NULL, loc_text, strip_pa_tags
from _common.lookup_index import IndexKind, lookup

LOC_SKILL = 10
# LOC type 10 holds the skill name at str_id4 0 and its description at 1.
_LOC_DESCRIPTION_ID4 = 1
# Literals some skill.dbss records store instead of a description.
_KOREAN_PLACEHOLDERS = frozenset({"UNKNOWN", LOC_NULL})

_LEVEL_MASK = 0xFFFF


def split_skill_key(skill_key: int) -> tuple[int, int]:
    """`(skill_no, level)` of a skill key."""
    return skill_key >> 16, skill_key & _LEVEL_MASK


def skill_name(skill_no: int) -> str:
    """LOC type 10 name of a skill, then its Korean `skilltype.dbss` name, else ''.

    The Korean names come from the `SKILL_NAME_KR` lookup index, so a table
    needs no `skilltype.dbss` companion for them.
    """
    name = loc_text(LOC_SKILL, skill_no)
    if name:
        return name
    korean = lookup(IndexKind.SKILL_NAME_KR, skill_no)
    return korean if isinstance(korean, str) else ""


def skill_description(skill_no: int, description_kr: str) -> str:
    """LOC type 10 description of a skill, else its Korean `skill.dbss` text, else ''.

    Both have PA tags removed. The Korean text is the source of the LOC one on
    most skills, but guild skills store their effect text there instead (see
    docs/file-formats/skill_dbss.md).
    """
    text = loc_text(LOC_SKILL, skill_no, _LOC_DESCRIPTION_ID4)
    if text and text != LOC_NULL:
        return text
    korean = strip_pa_tags(description_kr).strip()
    return "" if korean in _KOREAN_PLACEHOLDERS else korean


def _skill_buffs(skill_key: int) -> tuple[int, ...]:
    linked = lookup(IndexKind.SKILL_BUFFS, skill_key)
    return linked if isinstance(linked, tuple) else ()


def skill_buff_ids(skill_keys: Iterable[int]) -> list[int]:
    """Buffs the given skills apply, in skill then slot order, each once.

    Read from the `SKILL_BUFFS` lookup index, so empty when it is not loaded.
    """
    return list(dict.fromkeys(buff_id for key in skill_keys for buff_id in _skill_buffs(key)))
