"""Buff icon paths and buff text shared by the buff tables.

`buff.dbss` and `buffsimply.bss` store the same icon paths, and every table
that names a buff (`buff.dbss`, `buffsimply.bss`, the `skill.dbss` Buffs
column) reads its English text from LOC type 5, keyed by buff ID. See
docs/file-formats/buff_dbss.md.
"""

from __future__ import annotations

import re

from _common.loc import loc_lookup

# Stored paths start at "New_Icon/", which lives under ui_texture/icon/.
BUFF_ICON_ROOT = "ui_texture/icon/"
LOC_BUFF_DESCRIPTION = 5

# Some records store this literal instead of leaving the path empty.
_ICON_PLACEHOLDER = "unknown"
# A few paths double a separator (`04_pc_skill//04_debuff`).
_REPEATED_SLASHES = re.compile(r"/{2,}")
# LOC type 5 stores this literal for buffs that have no description.
_LOC_NULL = "<null>"


def buff_icon_path(stored: str) -> str:
    """PAZ path for a stored buff icon, or an empty string when there is none."""
    path = _REPEATED_SLASHES.sub("/", stored.strip().replace("\\", "/")).lower()
    if not path or path == _ICON_PLACEHOLDER:
        return ""
    return f"{BUFF_ICON_ROOT}{path}"


def buff_loc_description(buff_id: int) -> str:
    """LOC type 5 text of a buff with PA tags intact, or '' on a miss or `<null>`."""
    text = loc_lookup(LOC_BUFF_DESCRIPTION, buff_id).strip()
    return "" if text == _LOC_NULL else text
