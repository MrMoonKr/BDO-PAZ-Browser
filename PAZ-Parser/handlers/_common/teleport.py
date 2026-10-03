"""Teleport points and the buffs that teleport to them.

A buff of effect type 23 names a `teleport.dbss` point by section
(`param_1`) and key (`param_2`); keys repeat across sections, so the lookup
indexes key a point by both, packed into one ID.
"""

from __future__ import annotations

from _common.lookup_index import IndexKind, lookup

TELEPORT_EFFECT_TYPE = 23
_KEY_BITS = 16
_KEY_LIMIT = 1 << _KEY_BITS


def teleport_point_id(section: int, key: int) -> int:
    """One ID for a (section, key) pair; keys must fit in 16 bits."""
    if not 0 <= key < _KEY_LIMIT or section < 0:
        raise ValueError(f"teleport point {section}/{key} does not fit a point ID")
    return section << _KEY_BITS | key


def teleport_buff_ids(section: int, key: int) -> tuple[int, ...]:
    """The buffs that teleport to a point, from the TELEPORT_BUFFS index; () when none."""
    buff_ids = lookup(IndexKind.TELEPORT_BUFFS, teleport_point_id(section, key))
    return buff_ids if isinstance(buff_ids, tuple) else ()


def teleport_buff_name_kr(buff_id: int) -> str:
    """The Korean name of a teleport buff, from the TELEPORT_BUFF_NAME_KR index; '' when absent."""
    name = lookup(IndexKind.TELEPORT_BUFF_NAME_KR, buff_id)
    return name if isinstance(name, str) else ""
