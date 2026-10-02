"""Display title of a headline buff, read from its description, and the
buffs applied with it that share that title.

Kept out of `handler.py` so the tests can import it (see "Unit Tests" in
docs/handler.md).
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence

from _common.pa_text import strip_pa_tags


# "<PAColor0xffe9bd23>[Blessing] Adventure's Boon<PAOldColor>\n..."
_TITLE_LINE = re.compile(r"(<PAColor0x[0-9a-fA-F]{8}>[^<\r\n]+<PAOldColor>)[ \t]*\r?\n")


def extract_title_pa(raw_description: str) -> str:
    """Title line of a headline buff with its colour tags, or an empty string.

    About 2,000 shown buffs open their description with their name on a
    coloured line of its own, followed by the effects. A description that is
    only that one line is an effect, not a title, so it yields nothing.
    """
    match = _TITLE_LINE.match(raw_description)
    if not match or not raw_description[match.end():].strip():
        return ""
    return match.group(1)


def extract_title(raw_description: str) -> str:
    """Display name of a headline buff as plain text, or an empty string."""
    return strip_pa_tags(extract_title_pa(raw_description)).strip()


def title_leaders(buff_lists: Iterable[Sequence[int]], titles: Mapping[int, str]) -> dict[int, int]:
    """Map each untitled buff to the titled buff it is applied with, when that is unambiguous.

    `buff_lists` are the buffs each skill applies together (`skill.dbss`
    buff_ids) and `titles` the buffs with a title of their own. A consumable
    applies a run of buffs through one skill, and only its headline buff
    carries the title (48723 `[Blessing] Adventure's Boon` for 48724 to
    48728). A buff applied together with headline buffs of more than one
    title gets no leader; when several leaders share the one title, the lowest
    buff ID wins.
    """
    leaders_by_buff: dict[int, set[int]] = {}
    for buff_ids in buff_lists:
        leaders = {buff_id for buff_id in buff_ids if buff_id in titles}
        if not leaders:
            continue
        for buff_id in buff_ids:
            if buff_id not in titles:
                leaders_by_buff.setdefault(buff_id, set()).update(leaders)

    return {
        buff_id: min(leaders)
        for buff_id, leaders in leaders_by_buff.items()
        if len({titles[leader] for leader in leaders}) == 1
    }
