"""How a dialog text line is shown: user-language text without client tags, and its voice.

Kept out of `handler.py` so tests can import it without loading the handler
registry.
"""

from __future__ import annotations

import re

from _common.loc import loc_lookup
from _common.pa_text import strip_pa_tags
from .parser import DialogTextLine, DialogTextPool

# Keyed (pool key, text_id, 0, 0).
_LOC_DIALOG_TEXT = 36
# Client markup such as {AudioVoice(...)} or {ChangeScene(...)}.
_TAG = re.compile(r"\{[^{}]*\}")
_VOICE = re.compile(r"\{AudioVoice\(([^)]*)\)\}", re.IGNORECASE)
# Line breaks are stored as the two characters "\n".
_LINE_BREAK = "\\n"


def tagged_text(text: str) -> str:
    """`text` without client tags, on one line; PA colour tags are kept."""
    return " ".join(_TAG.sub("", text).replace(_LINE_BREAK, " ").split())


def plain_text(text: str) -> str:
    """`text` without client or PA tags, on one line."""
    return " ".join(strip_pa_tags(tagged_text(text)).split())


def line_text_tagged(pool: DialogTextPool, line: DialogTextLine, has_loc: bool) -> str:
    """The line in the user's language with its PA tags, falling back to the Korean source."""
    localized = loc_lookup(_LOC_DIALOG_TEXT, pool.key, line.text_id, 0, 0) if has_loc else ""
    return tagged_text(localized or line.text)


def voice_name(line: DialogTextLine) -> str | None:
    match = _VOICE.search(line.text)
    return match.group(1) if match else None
