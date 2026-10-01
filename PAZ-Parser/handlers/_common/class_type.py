"""Player class types and their LOC type 21 names.

A class type is the number `getClassType()` returns: `0` Warrior, `4` Ranger,
`8` Sorceress, `32` Seraph. Skill tables store sets of them as a bit mask
where bit `n` is class type `n`. See docs/file-formats/skillsimply_dbss.md.
"""

from __future__ import annotations

from _common.loc import loc_text

LOC_CLASS = 21
# Every bit a class can use; skills open to all classes store this mask.
ALL_CLASSES_MASK = 0x7FFF_FFFF_FFFF


def class_name(class_type: int) -> str:
    """LOC type 21 name of a class type, else the number."""
    return loc_text(LOC_CLASS, class_type) or str(class_type)


def class_types_in_mask(class_mask: int) -> tuple[int, ...]:
    """The class types whose bits are set, lowest first."""
    return tuple(bit for bit in range(class_mask.bit_length()) if class_mask >> bit & 1)
