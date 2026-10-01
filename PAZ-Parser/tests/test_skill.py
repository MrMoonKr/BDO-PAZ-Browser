from __future__ import annotations

import pytest

import _common.skill as skill
from _common.lookup_index import IndexKind, clear_indexes, init_index

# Skill 57339 has a Korean skilltype.dbss name and, on client 3458, no LOC name.
_TELEPORT_SKILL = 57339
_TELEPORT_KR = "므로웨크의 미궁 입구 텔레포트"
_STUB_ENGLISH = "English name"
# Guild skill 65069 (Ample Storage Lv. 8) has a Korean description and no LOC one.
_GUILD_SKILL = 65069
_GUILD_KR = "- 효과\n<PAColor0xffe9bd23>길드 창고를 10칸 확장.<PAOldColor>"
_STUB_DESCRIPTION = "English description"


@pytest.fixture(autouse=True)
def _clear_indexes():
    clear_indexes()
    yield
    clear_indexes()


def _loc(names: dict[int, str]):
    return lambda str_type, str_id1, str_id4=0: names.get(str_id1, "") if str_type == skill.LOC_SKILL else ""


def _loc_descriptions(descriptions: dict[int, str]):
    return lambda str_type, str_id1, str_id4=0: (
        descriptions.get(str_id1, "") if str_type == skill.LOC_SKILL and str_id4 == 1 else ""
    )


def test_split_skill_key() -> None:
    assert skill.split_skill_key(1759 << 16 | 3) == (1759, 3)


def test_korean_name_fills_a_missing_loc_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skill, "loc_text", _loc({}))
    init_index(IndexKind.SKILL_NAME_KR, {_TELEPORT_SKILL: _TELEPORT_KR})

    assert skill.skill_name(_TELEPORT_SKILL) == _TELEPORT_KR


def test_loc_name_wins_over_the_korean_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skill, "loc_text", _loc({_TELEPORT_SKILL: _STUB_ENGLISH}))
    init_index(IndexKind.SKILL_NAME_KR, {_TELEPORT_SKILL: _TELEPORT_KR})

    assert skill.skill_name(_TELEPORT_SKILL) == _STUB_ENGLISH


def test_no_name_without_loc_or_index(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skill, "loc_text", _loc({}))

    assert skill.skill_name(_TELEPORT_SKILL) == ""


def test_loc_description_wins_over_the_korean_one(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skill, "loc_text", _loc_descriptions({_GUILD_SKILL: _STUB_DESCRIPTION}))

    assert skill.skill_description(_GUILD_SKILL, _GUILD_KR) == _STUB_DESCRIPTION


@pytest.mark.parametrize("loc_description", ["", "<null>"])
def test_korean_description_fills_a_missing_loc_one(monkeypatch: pytest.MonkeyPatch, loc_description: str) -> None:
    monkeypatch.setattr(skill, "loc_text", _loc_descriptions({_GUILD_SKILL: loc_description}))

    assert skill.skill_description(_GUILD_SKILL, _GUILD_KR) == "- 효과\n길드 창고를 10칸 확장."


@pytest.mark.parametrize("stored", ["", "UNKNOWN", "<null>"])
def test_korean_placeholders_are_no_description(monkeypatch: pytest.MonkeyPatch, stored: str) -> None:
    monkeypatch.setattr(skill, "loc_text", _loc_descriptions({}))

    assert skill.skill_description(_GUILD_SKILL, stored) == ""
