"""Inline text as the tables store it, next to the LOC text it falls back for.

The tables write a line break in their inline Korean text as the two
characters backslash and `n`, where LOC stores a real newline. On client 3458
that is 6,580 breaks in `buff.dbss` descriptions, 873 in `skill.dbss`
descriptions and 28 in `quest.dbss` objectives, and no other escape occurs.
Decoding it lets the Korean fallback read like the LOC text: titles split off
their first line, and search finds the text as shown.
"""

from __future__ import annotations

_ESCAPED_NEWLINE = "\\n"


def decode_inline_text(text: str) -> str:
    """`text` with each stored `\\n` escape turned into a real newline."""
    return text.replace(_ESCAPED_NEWLINE, "\n")
