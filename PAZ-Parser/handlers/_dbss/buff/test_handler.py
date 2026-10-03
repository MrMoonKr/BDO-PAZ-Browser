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
from _common.html import e
from _common.inline_text import decode_inline_text
from _common.lookup_index import IndexKind
from _common.pa_text import pa_html

from _dbss.buff.effect import EffectInput, effect_text, param_labels
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
                "tick_ms",
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
        # Summon: Keeper Marg: in game "Marg's attack damage 579%" and
        # "Recover 250 MP every 10 sec".
        TargetTest(
            col="buff_id",
            value=8992,
            expected={"effect_type": 45, "param_4": 5790000, "effect": "Attack Damage 579%"},
        ),
        TargetTest(
            col="buff_id",
            value=8973,
            expected={
                "effect_type": 4,
                "tick_ms": 10000,
                "effect": "Recover 250 MP/WP/SP every 10 sec",
            },
        ),
        # An alchemy stone retaliation buff: type 1 under condition 4.
        TargetTest(
            col="buff_id",
            value=57123,
            expected={"effect_type": 1, "condition_type": 4, "effect": "Retaliate 15 Fixed Damage when struck"},
        ),
        # High-quality Carrot refills a mount's stamina: type 4 with no tick.
        TargetTest(col="buff_id", value=50403, expected={"effect_type": 4, "tick_ms": 0, "effect": ""}),
        # Cartian Spell (41587): "[Co-op] Eliminating the Threats to Mediah
        # will automatically be accepted".
        TargetTest(
            col="buff_id",
            value=57217,
            expected={"effect_type": 69, "effect": "Accept Quest: [Co-op] Eliminating the Threats to Mediah"},
        ),
        # Item 970013 summons character 28615.
        TargetTest(
            col="buff_id",
            value=48806,
            expected={"effect_type": 18, "param_1": 28615, "effect": "Summon Incarnation of Corruption"},
        ),
        # Item 66397 Tuntaros, used on pickup, unlocks knowledge 11216.
        TargetTest(
            col="buff_id",
            value=39562,
            expected={"effect_type": 38, "param_1": 11216, "effect": "Learn Knowledge: Tuntaros"},
        ),
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


def test_boon_titles_keep_their_game_colour(buff_result: HandlerResult) -> None:
    """The headline buff and the buffs that inherit its title draw it in colour."""
    records = [r for r in buff_result.records if r["buff_id"] in _BOON_BUFFS[:2]]

    assert len(records) == 2
    for record in records:
        html = pa_html(record["_title_pa"])
        assert html.startswith('<span class="pa-color" style="color: rgba(')
        assert e(_BOON_TITLE) in html


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
        # Life EXP names its life skill in param_3, 15 for all.
        (25, [150000, 2, 15], "Life EXP +15%"),
        # Hunter's Clothes (Costume) reads "Hunting EXP +10%" on bdocodex.
        (25, [100000, 2, 2], "Hunting EXP +10%"),
        (25, [100000, 0, 0], "Combat EXP +10%"),
        (39, [3, 8], "All AP +8"),
        (43, [3, -2], "All Damage Reduction -2"),
        (80, [4, 2560350], "Alchemy EXP +2,560,350"),
        (93, [4, 50000], "Critical Hit Extra Damage +5%"),
        (105, [8, 100000], "Ignore All Resistance +10%"),
        # Weight in ten-thousandths of an LT, durations in milliseconds.
        (29, [1000000, 0], "Weight Limit +100 LT"),
        (95, [15000, 0], "Underwater Breathing +15 sec"),
        # Pet skill 49134 reads "Death Penalty Resistance +3%".
        (90, [30000, 0], "Death Penalty Resistance +3%"),
        # One-off recoveries carry no sign.
        (63, [2, 0], "Recover 2 Worker Stamina"),
        (79, [10, 0], "Recover 10 Energy"),
        (67, [1, -1], "Attack Speed -1"),
        (89, [0, 2350], "Breath EXP +2,350"),
        # param_1 picks a rate or a flat amount.
        (120, [0, 60000], "Monster Damage Reduction Rate +6%"),
        (120, [2, 10], "Monster Damage Reduction +10"),
        # The amount sits in the parameter of its target.
        (136, [30, 0], "Extra AP Against Monsters +30"),
        (136, [0, 6], "Extra AP Against Adventurers +6"),
        (149, [2, 1, 70], "Hunting Mastery +70"),
        (149, [15, 0, 100], "Life Skill Mastery +100"),
        # A [Life Skill Season] single-tool mastery.
        (149, [0, 2, 580], ""),
        # Targets other than 3 (all) have no confirmed label.
        (39, [0, 8], ""),
        # A zero amount.
        (43, [3, 0], ""),
        (46, [3, -12], "Extra AP Against Kamasylvian Monsters -12"),
        (49, [8, 100000], "All Resistance +10%"),
        # Kind 6 (bound) reads "Not in Use".
        (49, [6, 100000], ""),
        # Damage is a share of attack, printed without a sign.
        (45, [2, 0, 0, 5790000], "Attack Damage 579%"),
        # A reduction stored positive: "Fall Damage -50%".
        (52, [500000, 0], "Fall Damage -50%"),
        # Centimetres: Chenga - Sherekhan Tome of Wisdom reads +150m.
        (53, [15000, 0], "Discovery Radius +150m"),
        (59, [80, 0], "Jump Height +80"),
        (91, [100000, 0], "Durability Reduction Resistance +10%"),
        # Time cuts per million of 20 sec: Eileen's Cheer, Alchemy Time -5 sec.
        (111, [0, 250000], "Alchemy Time -5 sec"),
        (111, [1, 15000], "Cooking Time -0.3 sec"),
        (111, [2, 80000], "Processing Success Rate +8%"),
        # Farming time does not fit the scale.
        (111, [3, 400000], ""),
        # Light Iron Horseshoe +0 and Epheria: Old Wind Sail on bdocodex.
        (98, [1, 20000], "Movement Speed (Mount) +2%"),
        (98, [2, 5000], "Turn +0.5%"),
        (98, [0, 10000], "Acceleration +1%"),
        (98, [3, 30000], "Brake +3%"),
        (187, [200, 0, 2], "AP +200"),
        (187, [250, 500, 1], "AP +250, DP +500"),
        (187, [0, -100, 0], "DP -100"),
        # A character or knowledge entry with no LOC name falls back to its ID.
        (18, [27542, 0], "Summon 27542"),
        (69, [11485, 30], "Accept Quest: 11485/30"),
        (38, [15074, 0], "Learn Knowledge: 15074"),
        (37, [2070, 0], "Register Node: 2070"),
        (142, [3176, 0], "Obtain Title: 3176"),
        # No table names a teleport point, so it always shows the key.
        (23, [0, 340], "Teleport to point 340"),
        # A kind outside the confirmed ones.
        (80, [10, 100], ""),
        # An effect type that is not decoded.
        (45, [1, 2], ""),
    ],
)
def test_effect_text(effect_type: int, params: list[int], expected: str) -> None:
    assert effect_text(EffectInput(effect_type, params)) == expected


@pytest.mark.parametrize(
    ("icon_path", "duration_ms", "expected"),
    [
        ("ui_texture/icon/new_icon/dot_poison.dds", 10000, "200 poison damage every 2 sec for 10 sec"),
        ("ui_texture/icon/new_icon/dot_burns.dds", 0, "200 burn damage every 2 sec"),
        # The bleeding icon also marks "burn" texts, so it names no kind.
        ("ui_texture/icon/new_icon/dot_bleeding.dds", 10000, "HP -200 every 2 sec"),
    ],
)
def test_ticking_damage_kind(icon_path: str, duration_ms: int, expected: str) -> None:
    buff = EffectInput(1, [-200], tick_ms=2000, duration_ms=duration_ms, icon_path=icon_path)
    text = effect_text(buff)
    assert text == expected


@pytest.mark.parametrize(
    ("effect_type", "amount", "tick_ms", "condition_type", "expected"),
    [
        (4, 250, 10000, 0, "Recover 250 MP/WP/SP every 10 sec"),
        (4, -50, 5000, 0, "MP/WP/SP -50 every 5 sec"),
        (4, 25, 1500, 0, "Recover 25 MP/WP/SP every 1.5 sec"),
        (4, 9, 0, 1, "Recover 9 MP/WP/SP on Hits"),
        # No tick and no condition: a one-off refill, possibly a mount's.
        (4, 500, 0, 0, ""),
        # A condition with no confirmed wording for MP/WP/SP.
        (4, 5, 0, 9, ""),
        (1, 25, 1000, 0, "Recover 25 HP every 1 sec"),
        # Poison, burn, pain and bleed differ only by icon.
        (1, -200, 1000, 0, "HP -200 every 1 sec"),
        (1, 9, 0, 1, "Recover 9 HP on Hits"),
        (1, 15, 0, 9, "Recover 15 HP on Critical Hits"),
        (1, -15, 0, 4, "Retaliate 15 Fixed Damage when struck"),
        (1, -7, 0, 6, "Deal 7 Fixed Damage on Back Attack Hits"),
        (1, -30, 0, 10, "Deal 30 Fixed Damage on Critical Hits"),
        # Infinite Fortitude: "Recover 250 HP when struck".
        (1, 250, 0, 3, "Recover 250 HP when struck"),
        # Fury of the Beast: "Recover 5 WP each time when struck".
        (4, 5, 0, 8, "Recover 5 MP/WP/SP when struck"),
        # A condition with no confirmed wording.
        (1, -100, 0, 2, ""),
    ],
)
def test_over_time_text(
    effect_type: int, amount: int, tick_ms: int, condition_type: int, expected: str
) -> None:
    buff = EffectInput(effect_type, [amount], tick_ms=tick_ms, condition_type=condition_type)
    assert effect_text(buff) == expected


@pytest.mark.parametrize(
    ("buff", "expected"),
    [
        # A kind parameter gets its kind; a flat amount needs no label.
        (EffectInput(46, [3, -12]), {1: "Kamasylvian Monsters"}),
        # A scaled amount shows the game's number.
        (EffectInput(9, [25000]), {1: "2.5%"}),
        (EffectInput(25, [150000, 0]), {1: "15%", 2: "Combat"}),
        # The parameter alone does not say which target it is.
        (EffectInput(136, [10, 0]), {1: "Monster AP"}),
        (EffectInput(136, [0, 6]), {2: "Adventurer AP"}),
        (EffectInput(120, [0, 15000]), {1: "Rate", 2: "1.5%"}),
        (EffectInput(149, [6, 1, 5]), {1: "Training"}),
        (EffectInput(4, [250], tick_ms=10000), {1: "every 10 sec"}),
        (EffectInput(1, [-15], condition_type=4), {1: "when struck"}),
        # No confirmed meaning: no labels at all.
        (EffectInput(39, [0, 8]), {}),
        (EffectInput(14, [6, 1350]), {}),
        (EffectInput(187, [0, 300, 2]), {3: "Earth"}),
        (EffectInput(25, [100000, 2, 2]), {1: "10%", 2: "Life", 3: "Hunting"}),
        (EffectInput(53, [1000]), {1: "10m"}),
        # A named effect without a name labels nothing.
        (EffectInput(23, [0, 340]), {}),
    ],
)
def test_param_labels(buff: EffectInput, expected: dict[int, str]) -> None:
    assert param_labels(buff) == expected


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
