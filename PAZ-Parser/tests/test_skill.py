from __future__ import annotations

import pytest

import _common.skill as skill
from _common.lookup_index import IndexKind, clear_indexes, init_index

# Skill 57339 has a Korean skilltype.dbss name and, on client 3458, no LOC name.
_TELEPORT_SKILL = 57339
_TELEPORT_KR = "므로웨크의 미궁 입구 텔레포트"
_STUB_ENGLISH = "English name"
# Guild skill 65069 (Ample Storage Lv. 8) has a Korean description, no LOC
# type 10 one, and its English in LOC type 13.
_GUILD_SKILL = 65069
_GUILD_KR = "- 효과\n<PAColor0xffe9bd23>길드 창고를 10칸 확장.<PAOldColor>"
_GUILD_EN = "- Effect:\n<PAColor0xffe9bd23>Adds 10 slots to the Guild Storage.<PAOldColor>"
_STUB_DESCRIPTION = "English description"


@pytest.fixture(autouse=True)
def _clear_indexes():
    clear_indexes()
    yield
    clear_indexes()


def _loc(names: dict[int, str]):
    return lambda str_type, str_id1, str_id4=0: names.get(str_id1, "") if str_type == skill.LOC_SKILL else ""


def _use_descriptions(
    monkeypatch: pytest.MonkeyPatch,
    skill_texts: dict[int, str],
    rank_texts: dict[tuple[int, int], str],
) -> None:
    """LOC type 10 descriptions by skill number and type 13 rank texts by (skill number, level)."""
    monkeypatch.setattr(
        skill,
        "loc_tagged",
        lambda str_type, str_id1, str_id4=0: (
            skill_texts.get(str_id1, "") if str_type == skill.LOC_SKILL and str_id4 == 1 else ""
        ),
    )
    monkeypatch.setattr(
        skill,
        "loc_lookup",
        lambda str_type, str_id1, str_id2=0, str_id3=0, str_id4=0: (
            rank_texts.get((str_id1, str_id2), "") if str_type == skill.LOC_SKILL_RANK else ""
        ),
    )


def test_split_skill_key() -> None:
    assert skill.split_skill_key(1759 << 16 | 3) == (1759, 3)


def test_korean_name_fills_a_missing_loc_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skill, "loc_tagged", _loc({}))
    init_index(IndexKind.SKILL_NAME_KR, {_TELEPORT_SKILL: _TELEPORT_KR})

    assert skill.skill_name(_TELEPORT_SKILL) == _TELEPORT_KR


def test_loc_name_wins_over_the_korean_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skill, "loc_tagged", _loc({_TELEPORT_SKILL: _STUB_ENGLISH}))
    init_index(IndexKind.SKILL_NAME_KR, {_TELEPORT_SKILL: _TELEPORT_KR})

    assert skill.skill_name(_TELEPORT_SKILL) == _STUB_ENGLISH


def test_no_name_without_loc_or_index(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skill, "loc_tagged", _loc({}))

    assert skill.skill_name(_TELEPORT_SKILL) == ""


def test_tagged_name_keeps_its_colour(monkeypatch: pytest.MonkeyPatch) -> None:
    tagged = "<PAColor0xffeb9261>Prime: Engage<PAOldColor>"
    monkeypatch.setattr(skill, "loc_tagged", _loc({_TELEPORT_SKILL: tagged}))

    assert skill.skill_name_tagged(_TELEPORT_SKILL) == tagged
    assert skill.skill_name(_TELEPORT_SKILL) == "Prime: Engage"


def test_skill_text_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_descriptions(monkeypatch, {_GUILD_SKILL: _STUB_DESCRIPTION}, {})

    assert skill.skill_description(_GUILD_SKILL, 1, _GUILD_KR) == _STUB_DESCRIPTION


def test_rank_text_replaces_the_korean_one(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_descriptions(monkeypatch, {_GUILD_SKILL: "<null>"}, {(_GUILD_SKILL, 1): _GUILD_EN})

    assert skill.skill_description_tagged(_GUILD_SKILL, 1, _GUILD_KR) == _GUILD_EN


def test_rank_text_is_read_for_the_rank_level(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_descriptions(monkeypatch, {}, {(_GUILD_SKILL, 2): _GUILD_EN})

    assert skill.skill_description_tagged(_GUILD_SKILL, 2, "") == _GUILD_EN
    assert skill.skill_description_tagged(_GUILD_SKILL, 1, "") == ""


def test_skill_text_then_a_different_rank_text(monkeypatch: pytest.MonkeyPatch) -> None:
    hint = "{TextBind:CASTING_CLICK_RMB} after learning the skill"
    _use_descriptions(monkeypatch, {_GUILD_SKILL: hint}, {(_GUILD_SKILL, 1): _GUILD_EN})

    assert skill.skill_description_tagged(_GUILD_SKILL, 1, _GUILD_KR) == f"{hint}\n\n{_GUILD_EN}"


def test_rank_text_equal_to_the_skill_text_shows_once(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_descriptions(
        monkeypatch,
        {_GUILD_SKILL: "Can register Exploration Node."},
        {(_GUILD_SKILL, 1): "<PAColor0xffe9bd23>Can register\nExploration Node.<PAOldColor>"},
    )

    assert skill.skill_description(_GUILD_SKILL, 1, "") == "Can register Exploration Node."


@pytest.mark.parametrize("loc_text", ["", "<null>", "0"])
def test_korean_description_fills_missing_loc_texts(monkeypatch: pytest.MonkeyPatch, loc_text: str) -> None:
    _use_descriptions(monkeypatch, {_GUILD_SKILL: loc_text}, {(_GUILD_SKILL, 1): loc_text})

    assert skill.skill_description(_GUILD_SKILL, 1, _GUILD_KR) == "- 효과\n길드 창고를 10칸 확장."


def test_korean_description_never_joins_an_english_one(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_descriptions(monkeypatch, {_GUILD_SKILL: _STUB_DESCRIPTION}, {})

    assert skill.skill_description(_GUILD_SKILL, 1, _GUILD_KR) == _STUB_DESCRIPTION


@pytest.mark.parametrize("stored", ["", "UNKNOWN", "<null>"])
def test_korean_placeholders_are_no_description(monkeypatch: pytest.MonkeyPatch, stored: str) -> None:
    _use_descriptions(monkeypatch, {}, {})

    assert skill.skill_description(_GUILD_SKILL, 1, stored) == ""


def test_korean_description_keeps_its_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_descriptions(monkeypatch, {}, {})

    assert skill.skill_description_tagged(_GUILD_SKILL, 1, _GUILD_KR) == _GUILD_KR
