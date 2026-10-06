"""The fixed run of function slots in every `characterfunction.dbss` record.

A record is a 4-byte head, 37 function slots in the order below, then a 7-byte
tail. A slot is two u64-prefixed UTF-16LE strings, the button text (`name`) and
its `condition` script, followed by the slot's own fields. Three slots store
the condition first. With every string empty a record is 732 bytes; the
`unknown_<hex>` names are offsets in that all-empty record.

`loc_index` is `str_id4` of the button text in LOC type 32 (`str_id1` is the
character ID). Slots the client gives no LOC text have `None`.
Full layout in docs/file-formats/characterfunction_dbss.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FieldKind = Literal["u8", "u16", "u32", "u8[]", "u32[]", "skip"]


@dataclass(frozen=True)
class FieldSpec:
    name: str
    kind: FieldKind
    # Byte count of a "skip" span, which the parser passes over; unused by the other kinds.
    size: int = 0


@dataclass(frozen=True)
class SlotSpec:
    key: str
    loc_index: int | None
    fields: tuple[FieldSpec, ...] = ()
    condition_first: bool = False


def _u8(name: str) -> FieldSpec:
    return FieldSpec(name, "u8")


def _u16(name: str) -> FieldSpec:
    return FieldSpec(name, "u16")


def _u32(name: str) -> FieldSpec:
    return FieldSpec(name, "u32")


# On most slots a u8 after the strings is 1 exactly when the slot has button text.
_HAS_BUTTON = _u8("has_button")

HEAD_FIELDS: tuple[FieldSpec, ...] = (
    _u8("unknown_000"),
    _u8("unknown_001"),
    _u8("unknown_002"),
    _u8("unknown_003"),
)

SLOTS: tuple[SlotSpec, ...] = (
    SlotSpec("shop", 0, (_u32("unknown_014"),)),
    SlotSpec("unknown_018", None, (_u32("unknown_028"),)),
    SlotSpec("guild_shop", 4, (_u32("unknown_03c"),)),
    SlotSpec("unknown_040", None, (_u32("unknown_050"),)),
    SlotSpec("trade", 2, (_u32("unknown_064"),)),
    SlotSpec(
        "auction",
        6,
        (
            _u32("unknown_078"),
            FieldSpec("unknown_07c", "skip", 14),
            _u32("unknown_08a"),
            FieldSpec("unknown_08e", "skip", 32),
        ),
    ),
    SlotSpec("learn_skill", 10, (_HAS_BUTTON,)),
    SlotSpec("repair", 11, (_HAS_BUTTON,)),
    SlotSpec("traces_of_blood", None, (_HAS_BUTTON,)),
    SlotSpec("storage", 12, (_HAS_BUTTON,)),
    SlotSpec("stable", 13, (_u8("unknown_102"), FieldSpec("unknown_103", "u8[]"))),
    SlotSpec("transport", 14, (_HAS_BUTTON,)),
    SlotSpec("unknown_118", None, (_HAS_BUTTON,)),
    SlotSpec("conversation", 16, (_HAS_BUTTON, _u8("unknown_13a"))),
    SlotSpec("create_guild", 17, (_HAS_BUTTON,)),
    SlotSpec(
        "node_management",
        18,
        (FieldSpec("managed_node_keys", "u32[]"), FieldSpec("town_node_keys", "u32[]")),
    ),
    SlotSpec("lord_information", 19, (_HAS_BUTTON,)),
    SlotSpec("unknown_175", None, (_HAS_BUTTON, _u8("unknown_186"))),
    SlotSpec("extraction", 21, (_HAS_BUTTON,)),
    SlotSpec("imperial_delivery", 23, (_u16("unknown_1a8"),)),
    SlotSpec("unknown_1aa", None, (_u16("unknown_1ba"),)),
    SlotSpec("knowledge_management", 24, (_HAS_BUTTON,)),
    SlotSpec("imperial_crafting_delivery", 25, (_HAS_BUTTON, _u8("unknown_1de"))),
    SlotSpec("imperial_fishing_delivery", 26, (_HAS_BUTTON,)),
    SlotSpec("unknown_1f0", None, (_HAS_BUTTON,)),
    SlotSpec("skill_addon", 28, (_HAS_BUTTON, _u8("unknown_212"))),
    SlotSpec("give_gift", 29, (_HAS_BUTTON,), condition_first=True),
    SlotSpec("cleanse_gear", 30, (_HAS_BUTTON,), condition_first=True),
    SlotSpec("black_spirit_adventure", None, (_HAS_BUTTON,), condition_first=True),
    SlotSpec("central_market", 31, (_u16("unknown_256"),)),
    SlotSpec("maritime_trade", None, (_u16("unknown_268"),)),
    SlotSpec(
        "hire_sailor",
        32,
        (_u8("unknown_27a"), _HAS_BUTTON, _u8("unknown_27c"), _u16("unknown_27d")),
    ),
    SlotSpec("season_special_gift", 34, (_u8("unknown_28f"),)),
    SlotSpec("hall_of_honor", 35, (_HAS_BUTTON,)),
    SlotSpec("yar", 36, (_u8("unknown_2b1"),)),
    SlotSpec("pet_training", 38, (_HAS_BUTTON, _u8("unknown_2c3"))),
    SlotSpec("lightstone", 39, (_u8("unknown_2d4"),)),
)

TAIL_FIELDS: tuple[FieldSpec, ...] = (
    _u8("unknown_2d5"),
    _u8("unknown_2d6"),
    _u32("unknown_2d7"),
    _u8("unknown_2db"),
)
