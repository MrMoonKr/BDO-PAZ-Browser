from __future__ import annotations

import struct
import zlib
from collections.abc import Mapping
from types import MappingProxyType

from _common.binary import u32
from _common.data_deps import LOC, note_read
# Re-exported: handlers import strip_pa_tags from here.
from _common.pa_text import strip_pa_tags as strip_pa_tags

# Some LOC keys store this literal instead of a text.
LOC_NULL = "<null>"


def decompress_loc(raw: bytes) -> bytes | None:
    try:
        return zlib.decompress(raw[4:])
    except Exception:
        return None


# ── Module-level indices (populated by init_loc) ─────────────────────────────

# (str_type, str_id1, str_id2, str_id3, str_id4) → text
_LOC_INDEX: dict[tuple[int, int, int, int, int], str] | None = None
# (str_type, str_id1) -> text values in file order
_LOC_PREFIX: dict[tuple[int, int], list[str]] | None = None
# str_type -> its keys and texts, built on the first `loc_type_entries()` call
# for the `_LOC_INDEX` held in `_LOC_BY_TYPE_SOURCE`
_LOC_BY_TYPE: dict[int, Mapping[tuple[int, int, int, int, int], str]] = {}
_LOC_BY_TYPE_SOURCE: object | None = None


def init_loc(raw: bytes | None) -> None:
    """Parse a languagedata_*.loc file. Pass None to clear all LOC data."""
    global _LOC_INDEX, _LOC_PREFIX, _LOC_BY_TYPE_SOURCE

    # Let go of the old index's per-type copies now, not on the next lookup.
    _LOC_BY_TYPE.clear()
    _LOC_BY_TYPE_SOURCE = None
    if raw is None:
        _LOC_INDEX = None
        _LOC_PREFIX = None
        return

    data = decompress_loc(raw)
    if data is None:
        return

    index:     dict[tuple[int, int, int, int, int], str] = {}
    prefix:    dict[tuple[int, int], list[str]] = {}

    pos = 0
    while pos + 16 <= len(data):
        str_size = u32(data, pos)
        str_type = u32(data, pos + 4)
        str_id1  = u32(data, pos + 8)
        str_id2  = struct.unpack_from("<H", data, pos + 12)[0]
        str_id3  = data[pos + 14]
        str_id4  = data[pos + 15]
        text_end = pos + 16 + str_size * 2

        if text_end + 4 > len(data):
            break

        text = data[pos + 16:text_end].decode("utf-16-le", errors="replace")
        pos = text_end + 4

        index[(str_type, str_id1, str_id2, str_id3, str_id4)] = text
        prefix.setdefault((str_type, str_id1), []).append(text)

    _LOC_INDEX  = index
    _LOC_PREFIX = prefix


# ── Public API ────────────────────────────────────────────────────────────────

def is_loc_loaded() -> bool:
    note_read(LOC)
    return _LOC_INDEX is not None


def loc_lookup(
    str_type: int,
    str_id1: int,
    str_id2: int = 0,
    str_id3: int = 0,
    str_id4: int = 0,
) -> str:
    """Return matching string or '' on miss / not loaded."""
    note_read(LOC)
    if _LOC_INDEX is None:
        return ""
    return _LOC_INDEX.get((str_type, str_id1, str_id2, str_id3, str_id4), "")


def loc_tagged(str_type: int, str_id1: int, str_id4: int = 0) -> str:
    """Text for a LOC key with its PA tags kept, for `pa_fields`, or '' on miss / not loaded."""
    return loc_lookup(str_type, str_id1, 0, 0, str_id4).strip()


def loc_text(str_type: int, str_id1: int, str_id4: int = 0) -> str:
    """Display text for a LOC key with PA tags removed, or '' on miss / not loaded."""
    return strip_pa_tags(loc_tagged(str_type, str_id1, str_id4)).strip()


def loc_lookup_prefix(str_type: int, str_id1: int) -> list[str]:
    """Return all strings matching a type/id1 pair in LOC index order."""
    note_read(LOC)
    if _LOC_PREFIX is None:
        return []

    return list(_LOC_PREFIX.get((str_type, str_id1), []))


def loc_type_entries(str_type: int) -> Mapping[tuple[int, int, int, int, int], str]:
    """Every key of one type with its text, read-only, or empty when not loaded.

    For types whose keys hold a part no caller knows up front, such as the
    service code in `str_id3` of type 50. The first call per type walks the
    whole index once.
    """
    global _LOC_BY_TYPE_SOURCE

    note_read(LOC)
    if _LOC_INDEX is None:
        return MappingProxyType({})
    if _LOC_BY_TYPE_SOURCE is not _LOC_INDEX:
        _LOC_BY_TYPE.clear()
        _LOC_BY_TYPE_SOURCE = _LOC_INDEX
    entries = _LOC_BY_TYPE.get(str_type)
    if entries is None:
        entries = MappingProxyType({key: text for key, text in _LOC_INDEX.items() if key[0] == str_type})
        _LOC_BY_TYPE[str_type] = entries
    return entries
