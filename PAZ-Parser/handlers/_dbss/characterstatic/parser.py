"""`characterstatic.dbss` records, located through `characterstaticoffset.dbss`.

Each offset row points just past a two-byte inline copy of the character ID.
The payload opens with two length-prefixed scripts, then the ID again:

    u8[8] header | u8 tag 0x15 | action_script | condition_script
    | u8 | u16 character_id | u16 | u32 npc_kind | ... | u8 class_type @ end-23

Both scripts are an i64 UTF-16 code-unit count followed by UTF-16LE text.
Full layout in docs/file-formats/characterstatic_dbss.md.
"""

from __future__ import annotations

import re
import struct

from _common.pabr_offset import PabrOffsetRow

_TAG = 0x08
_TAG_VALUE = 0x15
_ACTION_SCRIPT = 0x09
# From the first byte after condition_script.
_CHARACTER_ID = 0x01
_NPC_KIND = 0x05
_AFTER_SCRIPTS_SIZE = _NPC_KIND + 4
# From the end of the payload.
_CLASS_TYPE_FROM_END = 23
# class_type on every row that is not a player character.
NO_CLASS_TYPE = 101

_I64 = struct.Struct("<q")
_GETKNOWLEDGE_RE = re.compile(r"getknowledge\((\d+)\)", re.IGNORECASE)


def _read_script(data: bytes, pos: int, end: int, character_id: int) -> tuple[str, int]:
    """Read an i64-prefixed UTF-16LE script; return it and the next position."""
    (length,) = _I64.unpack_from(data, pos)
    text_end = pos + _I64.size + 2 * length
    if length < 0 or text_end > end:
        raise ValueError(f"character {character_id} has a script that runs past its record")
    return data[pos + _I64.size:text_end].decode("utf-16-le"), text_end


def _parse_record(data: bytes, row: PabrOffsetRow) -> dict:
    start = row.offset
    end = start + row.size
    character_id = row.entry_id
    if end > len(data) or row.size < _CLASS_TYPE_FROM_END:
        raise ValueError(f"character {character_id} runs past the end of characterstatic.dbss")
    if data[start + _TAG] != _TAG_VALUE:
        raise ValueError(f"character {character_id} record does not carry the 0x15 tag")

    action_script, pos = _read_script(data, start + _ACTION_SCRIPT, end, character_id)
    condition_script, pos = _read_script(data, pos, end, character_id)
    if pos + _AFTER_SCRIPTS_SIZE > end:
        raise ValueError(f"character {character_id} ends inside its fixed fields")
    if struct.unpack_from("<H", data, pos + _CHARACTER_ID)[0] != character_id:
        raise ValueError(f"character {character_id} record does not repeat its own ID")

    match = _GETKNOWLEDGE_RE.search(action_script)
    return {
        "character_id": character_id,
        "action_script": action_script,
        "condition_script": condition_script,
        "knowledge_id": int(match.group(1)) if match else None,
        "npc_kind": struct.unpack_from("<I", data, pos + _NPC_KIND)[0],
        "class_type": data[end - _CLASS_TYPE_FROM_END],
        "payload_size": row.size,
    }


def parse_characterstatic_records(data: bytes, rows: list[PabrOffsetRow]) -> list[dict]:
    """Parse every record the offset table points at, in offset-table order.

    Raises ValueError on the first malformed record: after a bad script length
    every later field would be misread.
    """
    return [_parse_record(data, row) for row in rows]
