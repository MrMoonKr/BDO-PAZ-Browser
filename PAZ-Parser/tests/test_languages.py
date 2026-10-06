"""The game languages, their LOC files and the missing-LOC warning."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import api.bdo_api_caches as caches
import api.bdo_config as bdo_config
import ui_text
from api.bdo_api import Api
from api.bdo_languages import GAME_LANGUAGES, LOC_FOLDER, UI_LANGUAGES, missing_loc_file

_LANG_DIR = Path(ui_text.__file__).parent / "ui" / "lang"


@pytest.fixture
def config_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "paz_config.json"
    monkeypatch.setattr(bdo_config, "CONFIG_FILE", path)
    return path


@pytest.fixture
def paz_root(tmp_path: Path) -> Path:
    """A client with only the English LOC file."""
    root = tmp_path / "Paz"
    root.mkdir()
    (tmp_path / LOC_FOLDER).mkdir()
    (tmp_path / LOC_FOLDER / "languagedata_en.loc").write_bytes(b"")
    return root


@pytest.fixture
def installed_loc(monkeypatch: pytest.MonkeyPatch) -> list[bytes | None]:
    """The LOC text each `_install_loc` call installs, without parsing it."""
    installed: list[bytes | None] = []
    monkeypatch.setattr(caches, "init_loc", installed.append)
    return installed


def _api(paz_root: Path, config_file: Path, language: str) -> Api:
    config_file.write_text(json.dumps({"language": language}))
    api = Api()
    api._paz_root = paz_root
    return api


# ── The language list ────────────────────────────────────────────────────────

def test_codes_and_game_types_are_unique() -> None:
    assert len({language.code for language in GAME_LANGUAGES}) == len(GAME_LANGUAGES)
    assert len({language.pa_type for language in GAME_LANGUAGES}) == len(GAME_LANGUAGES)


def test_the_ui_languages_are_the_shipped_language_files() -> None:
    shipped = {path.stem for path in _LANG_DIR.glob("*.json")}

    assert {language.code for language in UI_LANGUAGES} == shipped


def test_every_ui_language_can_name_its_loc_file() -> None:
    unnamed = [language.code for language in UI_LANGUAGES if language.loc_file is None and not language.text_in_tables]

    assert unnamed == []


# ── missing_loc_file ─────────────────────────────────────────────────────────

def test_a_present_loc_file_is_not_missing(paz_root: Path) -> None:
    assert missing_loc_file(paz_root, "en") is None


def test_an_absent_loc_file_is_named(paz_root: Path) -> None:
    assert missing_loc_file(paz_root, "de") == "languagedata_de.loc"


def test_korean_needs_no_loc_file(paz_root: Path) -> None:
    assert missing_loc_file(paz_root, "kr") is None


# ── Api ──────────────────────────────────────────────────────────────────────

def test_the_warning_names_the_missing_file(paz_root: Path, config_file: Path) -> None:
    warning = _api(paz_root, config_file, "de").get_loc_warning()

    assert warning == {"language": "de", "name": "Deutsch", "file": "languagedata_de.loc"}


def test_no_warning_when_the_loc_file_is_there(paz_root: Path, config_file: Path) -> None:
    assert _api(paz_root, config_file, "en").get_loc_warning() == {}


def test_a_dismissed_warning_stays_closed(paz_root: Path, config_file: Path) -> None:
    api = _api(paz_root, config_file, "de")

    api.dismiss_loc_warning("de")

    assert api.get_loc_warning() == {}


def test_a_dismissed_warning_is_still_marked_in_the_settings(paz_root: Path, config_file: Path) -> None:
    api = _api(paz_root, config_file, "de")
    api.dismiss_loc_warning("de")

    assert api.get_settings()["missing_loc"]["de"] == "languagedata_de.loc"


def test_dismissing_an_unknown_language_saves_nothing(paz_root: Path, config_file: Path) -> None:
    api = _api(paz_root, config_file, "de")

    api.dismiss_loc_warning("xx")

    assert "loc_warning_dismissed" not in json.loads(config_file.read_text())


def test_the_settings_list_only_ui_languages(paz_root: Path, config_file: Path) -> None:
    listed = {language["code"] for language in _api(paz_root, config_file, "en").get_settings()["languages"]}

    assert listed == {language.code for language in UI_LANGUAGES}


def test_a_language_switch_shows_the_new_loc_file(paz_root: Path, installed_loc: list[bytes | None]) -> None:
    (paz_root.parent / LOC_FOLDER / "languagedata_ru.loc").write_bytes(b"russian")
    api = Api()
    api._paz_root = paz_root
    api._load_loc("en")

    api._load_loc("ru")

    assert list(api._disk_companions) == ["languagedata_ru.loc"]
    assert installed_loc[-1] == b"russian"


def test_a_language_without_a_loc_file_shows_none(paz_root: Path, installed_loc: list[bytes | None]) -> None:
    api = Api()
    api._paz_root = paz_root
    api._load_loc("en")

    api._load_loc("kr")

    assert api._loc_file_name() is None
    assert installed_loc[-1] is None


# ── Saving the settings ──────────────────────────────────────────────────────

def test_saving_the_same_language_keeps_the_loc_text(
    paz_root: Path, config_file: Path, installed_loc: list[bytes | None]
) -> None:
    api = _api(paz_root, config_file, "en")

    assert api.save_settings("", "en")["ok"] is True

    assert installed_loc == []


def test_saving_a_new_language_installs_its_loc_text(
    paz_root: Path, config_file: Path, installed_loc: list[bytes | None]
) -> None:
    api = _api(paz_root, config_file, "en")

    assert api.save_settings("", "de")["ok"] is True

    assert len(installed_loc) == 1
    assert json.loads(config_file.read_text())["language"] == "de"
