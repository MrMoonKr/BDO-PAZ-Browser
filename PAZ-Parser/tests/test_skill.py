from __future__ import annotations

import pytest

import _common.skill as skill
from _common.lookup_index import IndexKind, clear_indexes, init_index

# Skill 57339 has a Korean skilltype.dbss name and, on client 3458, no LOC name.
_TELEPORT_SKILL = 57339
_TELEPORT_KR = "므로웨크의 미궁 입구 텔레포트"
_STUB_ENGLISH = "English name"


@pytest.fixture(autouse=True)
def _clear_indexes():
    clear_indexes()
    yield
    clear_indexes()


def _loc(names: dict[int, str]):
    return lambda str_type, str_id1, str_id4=0: names.get(str_id1, "") if str_type == skill.LOC_SKILL_NAME else ""


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
