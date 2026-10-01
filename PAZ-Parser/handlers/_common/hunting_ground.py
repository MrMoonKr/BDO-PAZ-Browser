"""Drop item window hunting grounds by key.

`dropuihuntinggroundinfo.bss` holds one row per hunting ground, and
`worldmapmonster.dbss` points at its keys from the hunting zone markers. LOC
type 116 names a hunting ground by key. See
docs/file-formats/dropuihuntinggroundinfo_bss.md.
"""

from __future__ import annotations

from _common.loc import loc_text

LOC_HUNTING_GROUND_NAME = 116


def hunting_ground_name(key: int) -> str:
    """LOC type 116 name of a hunting ground, or '' when it has none or LOC is not loaded."""
    return loc_text(LOC_HUNTING_GROUND_NAME, key)
