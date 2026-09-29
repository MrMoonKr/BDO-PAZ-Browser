"""Display title of a headline buff, read from its description.

Kept out of `handler.py` so the tests can import it (see "Unit Tests" in
docs/handler.md).
"""

from __future__ import annotations

import re


# "<PAColor0xffe9bd23>[Blessing] Adventure's Boon<PAOldColor>\n..."
_TITLE_LINE = re.compile(r"<PAColor0x[0-9a-fA-F]{8}>([^<\r\n]+)<PAOldColor>[ \t]*\r?\n")


def extract_title(raw_description: str) -> str:
    """Display name of a headline buff, or an empty string.

    About 2,000 shown buffs open their description with their name on a
    coloured line of its own, followed by the effects. A description that is
    only that one line is an effect, not a title, so it yields nothing.
    """
    match = _TITLE_LINE.match(raw_description)
    if not match or not raw_description[match.end():].strip():
        return ""
    return match.group(1).strip()
