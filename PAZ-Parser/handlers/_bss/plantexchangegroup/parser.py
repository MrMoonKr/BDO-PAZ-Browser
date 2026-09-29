"""`plantexchangegroup.bss`: worker production groups.

    PABR | u32 count | count x 94-byte row | string table | u32 string_table_start | u32 0

Each row maps a production key (the `plantzone.dbss` join) to the
`itemsubgroup.dbss` subgroup of items the node produces, and carries a Korean
"node - work type" label. Full layout in docs/file-formats/plantexchangegroup_bss.md.
"""

from __future__ import annotations

import struct

from _common.binary import u32
from _common.pabr_strings import TRAILER_SIZE, read_string_table, string_at, string_table_start
from _dbss.itemsubgroup.parser import subgroups_by_key


_MAGIC = b"PABR"
_HEADER_SIZE = 8

# u16 production_key | u16 unknown_02 | u16 unknown_04 | u32 item_subgroup_key
# | 80 zero bytes | u32 name_ref
_RECORD = struct.Struct("<HHHI80xI")
_RECORD_SIZE = 94
assert _RECORD.size == _RECORD_SIZE


def parse_plantexchangegroup_records(data: bytes) -> list[dict]:
    """Every production group row in file order, with its label resolved.

    Raises ValueError on a bad magic, or when the rows do not end where the
    string table starts: then the row size has changed and every field is suspect.
    """
    if len(data) < _HEADER_SIZE + TRAILER_SIZE or data[:4] != _MAGIC:
        raise ValueError("plantexchangegroup.bss has invalid magic.")

    count = u32(data, 4)
    rows_end = _HEADER_SIZE + count * _RECORD_SIZE
    if rows_end != string_table_start(data):
        raise ValueError(
            f"plantexchangegroup.bss rows end at 0x{rows_end:X} but its string "
            f"table starts at 0x{string_table_start(data):X}"
        )

    strings = read_string_table(data)
    records: list[dict] = []
    for offset in range(_HEADER_SIZE, rows_end, _RECORD_SIZE):
        production_key, unknown_02, unknown_04, item_subgroup_key, name_ref = (
            _RECORD.unpack_from(data, offset)
        )
        records.append({
            "production_key": production_key,
            "unknown_02": unknown_02,
            "unknown_04": unknown_04,
            "item_subgroup_key": item_subgroup_key,
            "name_kr": string_at(strings, name_ref),
        })
    return records


def build_production_item_index(
    groups: bytes,
    subgroups: bytes,
    subgroup_offsets: bytes,
) -> dict[int, tuple[int, ...]]:
    """The `PRODUCTION_ITEMS` index: each production key to its subgroup's packed item keys.

    Only a few hundred of the 16,000+ subgroups are production subgroups, so the
    index holds just those instead of every table that shows production items
    opening the 13 MB `itemsubgroup.dbss`. Keys whose subgroup is missing from
    `itemsubgroupoffset.dbss` are left out.
    """
    rows = parse_plantexchangegroup_records(groups)
    found = subgroups_by_key(subgroups, subgroup_offsets, {row["item_subgroup_key"] for row in rows})
    return {
        row["production_key"]: found[row["item_subgroup_key"]].item_keys
        for row in rows
        if row["item_subgroup_key"] in found
    }
