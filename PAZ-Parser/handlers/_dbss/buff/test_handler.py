from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

import pytest

from tests.framework import (
    DeclaredCountTest,
    HandlerCase,
    HandlerResult,
    RangeTest,
    SchemaTest,
    TargetTest,
    case_id,
    header_count,
    run_case,
)

from _common.duration import format_duration
from _common.inline_text import decode_inline_text
from _common.lookup_index import IndexKind

from _dbss.buff.effect import effect_text
from _dbss.buff.title import extract_title, title_leaders


# Backslash and `n`, how the tables store a line break in inline text.
_ESCAPED_NEWLINE = "\\n"
# Item 761880, [Blessing] Adventure's Boon (120 min), casts skill 47683 level 1,
# which applies buffs 48723 to 48728; 48723 is the headline buff with the title.
_BOON_ITEM = 761880
_BOON_SKILL_KEY = 47683 << 16 | 1
_BOON_BUFFS = (48723, 48724, 48725, 48726, 48727, 48728)
_BOON_TITLE = "[Blessing] Adventure's Boon"


BUFF_CASE = HandlerCase(
    handler_name="buff.dbss",
    data_file="buff.dbss",
    companion_files={"buffoffset.dbss": "buffoffset.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["description"],
    internal_path="gamecommondata/binary/buff.dbss",
    lookup_indexes={
        IndexKind.SKILL_BUFFS: {_BOON_SKILL_KEY: _BOON_BUFFS},
        IndexKind.BUFF_ITEMS: {buff_id: (_BOON_ITEM,) for buff_id in _BOON_BUFFS},
    },
    tests=[
        SchemaTest(
            required_keys=[
                "buff_id",
                "name",
                "level",
                "effect_type",
                "duration_ms",
                "duration",
                "icon_path",
                "title",
                "title_buff_id",
                "description",
                "effect",
                "applied_by_item_ids",
                "applied_by",
                "applied_by_count",
                "description_kr",
                "param_1",
                "param_10",
                "is_shown",
                "apply_rate",
                "group",
                "condition_type",
                "stacking_category",
            ]
        ),
        DeclaredCountTest(declared=header_count()),
        TargetTest(
            col="buff_id",
            value=48879,
            expected={"name": "중범선 대미지 저항 18.9%", "effect_type": 106, "icon_path": ""},
        ),
        TargetTest(
            col="buff_id",
            value=48830,
            expected={
                "name": "수렵 숙련도 +70 3시간",
                "effect_type": 149,
                "icon_path": "ui_texture/icon/new_icon/04_pc_skill/03_buff/huntingbuff.dds",
                "description": "Hunting Mastery +70",
                "title": "",
                "is_shown": True,
            },
        ),
        # EXP gain: param_2 selects combat (0), skill (1) or life (2) EXP.
        TargetTest(col="buff_id", value=47692, expected={"effect_type": 25, "param_2": 0}),
        # Headline buff: the coloured first line of its description is its title.
        TargetTest(
            col="buff_id",
            value=48723,
            expected={
                "title": _BOON_TITLE,
                "title_buff_id": 48723,
                "name": "모든 공격력 +8(120분)",
                "is_shown": True,
                "effect": "All AP +8",
                "applied_by_item_ids": [_BOON_ITEM],
            },
        ),
        # The rest of the same item's buffs are hidden and have no text; they
        # take the headline buff's title through the skill that applies them.
        TargetTest(
            col="buff_id",
            value=48724,
            expected={
                "title": _BOON_TITLE,
                "title_buff_id": 48723,
                "description": "",
                "effect_type": 40,
                "effect": "All Accuracy +8",
                "is_shown": False,
            },
        ),
        TargetTest(col="buff_id", value=48727, expected={"effect": "Combat EXP +15%"}),
        # Applied by no item in the installed index: an empty list, None to sort last.
        TargetTest(
            col="buff_id",
            value=48830,
            expected={"applied_by_item_ids": [], "applied_by_count": None, "title_buff_id": None},
        ),
        # Food Max HP variants share one group.
        TargetTest(col="buff_id", value=59746, expected={"effect_type": 2, "group": 5616}),
        # Group keys from 40001 up are u16; an i16 read made them negative.
        RangeTest(col="group", min_val=0, max_val=0xFFFF),
        # Whale tendon elixirs have their own stacking category.
        TargetTest(col="buff_id", value=58025, expected={"stacking_category": 21}),
        RangeTest(col="level", min_val=0, max_val=math.inf),
        RangeTest(col="duration_ms", min_val=0, max_val=math.inf),
    ],
)

OFFSET_CASE = HandlerCase(
    handler_name="buffoffset.dbss",
    data_file="buffoffset.dbss",
    companion_files={},
    loc_file=None,
    uses_loc=False,
    loc_fields=[],
    internal_path="gamecommondata/binary/buffoffset.dbss",
    tests=[
        SchemaTest(required_keys=["buff_id", "offset", "size"]),
        DeclaredCountTest(declared=header_count(offset=4)),
        # The first record follows buff.dbss's u32 count.
        TargetTest(col="offset", value=4, expected={}),
    ],
)


@pytest.fixture(scope="module")
def buff_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_BUFF_RESULT", None)
    if result is None:
        result = run_case(replace(BUFF_CASE, tests=[]))
        request.module._BUFF_RESULT = result
    return result


@pytest.fixture(scope="module")
def offset_result(request: Any) -> HandlerResult:
    result = getattr(request.module, "_OFFSET_RESULT", None)
    if result is None:
        result = run_case(replace(OFFSET_CASE, tests=[]))
        request.module._OFFSET_RESULT = result
    return result


@pytest.mark.parametrize("spec", BUFF_CASE.tests, ids=case_id)
def test_buff_dbss(spec: Any, buff_result: HandlerResult) -> None:
    buff_result.check(spec)


@pytest.mark.parametrize("spec", OFFSET_CASE.tests, ids=case_id)
def test_buffoffset_dbss(spec: Any, offset_result: HandlerResult) -> None:
    offset_result.check(spec)


def test_buff_group_levels_are_unique(buff_result: HandlerResult) -> None:
    """Within a group, each level is held by one buff."""
    seen: set[tuple[int, int]] = set()
    for record in buff_result.records:
        if not record["group"]:
            continue
        key = (record["group"], record["level"])
        assert key not in seen, f"group {key[0]} has level {key[1]} twice"
        seen.add(key)


@pytest.mark.parametrize(
    ("duration_ms", "expected"),
    [
        (0, ""),
        (1500, "1.5s"),
        (30000, "30s"),
        (1200000, "20m"),
        (5400000, "1h 30m"),
        (86400000, "24h"),
    ],
)
def test_format_duration(duration_ms: int, expected: str) -> None:
    assert format_duration(duration_ms) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("<PAColor0xffe9bd23>Eileen's Cheer<PAOldColor>\n\n  Alchemy Time -5 sec", "Eileen's Cheer"),
        ("<PAColor0xffe9bd23>[축복] 모험의 가호<PAOldColor>\r\n모든 공격력 +8", "[축복] 모험의 가호"),
        # One line is an effect, not a title.
        ("Hunting Mastery <PAColor0xffe9bd23>+70<PAOldColor>", ""),
        ("<PAColor0xffe9bd23>Life EXP +3%<PAOldColor>", ""),
        ("<PAColor0xffe9bd23>Trailing only<PAOldColor>\n  ", ""),
        ("", ""),
    ],
)
def test_extract_title(raw: str, expected: str) -> None:
    assert extract_title(raw) == expected


def test_inline_descriptions_hold_no_newline_escapes(buff_result: HandlerResult) -> None:
    """The stored two-character escape is decoded, so the Korean text breaks lines like LOC."""
    escaped = [r["buff_id"] for r in buff_result.records if _ESCAPED_NEWLINE in r["description_kr"]]
    assert not escaped, f"descriptions still hold a newline escape: {escaped[:5]}"


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        (f"모든 공격력 +8{_ESCAPED_NEWLINE}모든 적중력 +8", "모든 공격력 +8\n모든 적중력 +8"),
        (_ESCAPED_NEWLINE * 2, "\n\n"),
        ("no escape", "no escape"),
        ("", ""),
    ],
)
def test_decode_inline_text(stored: str, expected: str) -> None:
    assert decode_inline_text(stored) == expected


def test_korean_title_survives_without_loc() -> None:
    stored = f"<PAColor0xffe9bd23>[축복] 모험의 가호<PAOldColor>{_ESCAPED_NEWLINE * 2}모든 공격력 +8"
    assert extract_title(decode_inline_text(stored)) == "[축복] 모험의 가호"


@pytest.mark.parametrize(
    ("effect_type", "params", "expected"),
    [
        (2, [150, 0], "Max HP +150"),
        (8, [-150, 0], "Max Stamina -150"),
        # Per-million percentages keep their decimals and drop trailing zeros.
        (9, [25000, 0], "Movement Speed +2.5%"),
        (25, [150000, 2], "Life EXP +15%"),
        (39, [3, 8], "All AP +8"),
        (43, [3, -2], "All Damage Reduction -2"),
        (80, [4, 2560350], "Alchemy EXP +2,560,350"),
        (93, [4, 50000], "Critical Hit Extra Damage +5%"),
        (105, [8, 100000], "Ignore All Resistance +10%"),
        # Targets other than 3 (all) have no confirmed label.
        (39, [0, 8], ""),
        # A kind outside the confirmed ones.
        (80, [10, 100], ""),
        # An effect type that is not decoded.
        (45, [1, 2], ""),
    ],
)
def test_effect_text(effect_type: int, params: list[int], expected: str) -> None:
    assert effect_text(effect_type, params) == expected


def test_title_leaders_follow_the_skill_that_applies_them() -> None:
    titles = {1: "Boon", 10: "Meal", 11: "Meal", 20: "Draught A", 21: "Draught B"}
    buff_lists = [
        (1, 2, 3),
        # Two headline buffs with one title: the lower ID leads.
        (11, 10, 12),
        # Two titles: the members are ambiguous and get none.
        (20, 21, 22),
        # No headline buff at all.
        (30, 31),
    ]
    assert title_leaders(buff_lists, titles) == {2: 1, 3: 1, 12: 10}


def test_title_leaders_drop_a_buff_reached_by_two_titles() -> None:
    titles = {1: "Boon", 5: "Meal"}
    assert title_leaders([(1, 2), (5, 2)], titles) == {}
