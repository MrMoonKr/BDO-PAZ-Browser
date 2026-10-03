from __future__ import annotations

from _common.loc import loc_lookup
from _common.pa_text import strip_pa_tags

LOC_QUEST = 18


def quest_title_tagged(quest_chain_id: int, quest_id: int) -> str:
    """LOC type 18 title of a quest with its PA tags, for `pa_fields`, or ''."""
    return loc_lookup(LOC_QUEST, quest_chain_id, quest_id, 0, 0).strip()


def quest_title(quest_chain_id: int, quest_id: int) -> str:
    return strip_pa_tags(quest_title_tagged(quest_chain_id, quest_id)).strip()
