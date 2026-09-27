from __future__ import annotations

import struct

import pytest

from _common.pabr_offset import parse_pabr_offset_rows
from _dbss.characterobject.parser import (
    CharacterObjectRecord,
    build_character_icon_index,
    parse_characterobject_records,
)

_FURNITURE = 2


def _record(character_id: int, model: bytes, icon: bytes = b"", kind: int = _FURNITURE) -> bytes:
    """Prefix, model path, then a u64-length-prefixed icon path."""
    prefix = struct.pack("<HB3x", character_id, kind)
    return prefix + struct.pack("<Q", len(model)) + model + struct.pack("<Q", len(icon)) + icon


def _tables(records: dict[int, bytes]) -> tuple[bytes, bytes]:
    data = bytearray(struct.pack("<I", len(records)))
    rows = bytearray()
    for character_id, block in records.items():
        rows += struct.pack("<HII", character_id, len(data), len(block))
        data += block
    offset = b"PABR" + struct.pack("<I", len(records)) + rows
    return bytes(data), offset


def test_parses_prefix_fields() -> None:
    data, offset = _tables({
        1001: _record(1001, b"00_Common/Crafting/Crafting_Smithing_01.pam"),
        2101: _record(2101, b"02_balenos/velia/balenos_velia_str_house_05.pam", kind=5),
    })

    records = parse_characterobject_records(data, parse_pabr_offset_rows(offset))

    assert records == [
        CharacterObjectRecord(1001, _FURNITURE, "00_Common/Crafting/Crafting_Smithing_01.pam"),
        CharacterObjectRecord(2101, 5, "02_balenos/velia/balenos_velia_str_house_05.pam"),
    ]


def test_rejects_record_whose_id_disagrees_with_offset_table() -> None:
    data, offset = _tables({1001: _record(1002, b"model.pam")})

    with pytest.raises(ValueError, match="offset table says 1001"):
        parse_characterobject_records(data, parse_pabr_offset_rows(offset))


def test_rejects_row_past_end_of_file() -> None:
    data, offset = _tables({1001: _record(1001, b"model.pam")})

    with pytest.raises(ValueError, match="runs past the end"):
        parse_characterobject_records(data[:-4], parse_pabr_offset_rows(offset))


def test_icon_path_hangs_off_ui_texture() -> None:
    data, offset = _tables({
        16111: _record(16111, b"m.pam", b"Icon/New_Icon/03_ETC/06_Housing/Pot_Base_48.dds"),
    })

    assert build_character_icon_index(data, offset) == {
        16111: "ui_texture/icon/new_icon/03_etc/06_housing/pot_base_48.dds",
    }


def test_new_icon_path_keeps_its_folder_level() -> None:
    # Stored one level lower; matching only the inner "Icon/" would drop
    # "new_icon/" and point at a file the client does not ship.
    data, offset = _tables({
        16228: _record(16228, b"m.pam", b"New_Icon/03_ETC/06_Housing/InHouse_X_DPW_Pic_20.dds"),
    })

    assert build_character_icon_index(data, offset) == {
        16228: "ui_texture/icon/new_icon/03_etc/06_housing/inhouse_x_dpw_pic_20.dds",
    }


def test_record_without_icon_is_skipped() -> None:
    data, offset = _tables({1001: _record(1001, b"00_Common/Pot/Pot_Base_48.pam")})

    assert build_character_icon_index(data, offset) == {}
