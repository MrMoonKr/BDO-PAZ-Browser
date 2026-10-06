"""UI text: the Python lookup, and every language file covering en.json."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

import ui_text as ui_text_module
from ui_text import set_ui_language, ui_text

from tests.lang_files import flat_strings, placeholders

_LANG_DIR = Path(ui_text_module.__file__).parent / "ui" / "lang"
_LANGUAGES = sorted(path.stem for path in _LANG_DIR.glob("*.json") if path.stem != "en")


@pytest.fixture(autouse=True)
def _english_after_each_test() -> Iterator[None]:
    yield
    set_ui_language("en")


def _strings(language: str) -> dict[str, str]:
    return flat_strings(_LANG_DIR / f"{language}.json")


def test_text_fills_placeholders() -> None:
    assert ui_text("errors.diskFileNotLoaded", name="a.loc").endswith("a.loc")


def test_a_missing_argument_keeps_its_placeholder() -> None:
    assert "{name}" in ui_text("errors.diskFileNotLoaded")


def test_an_unknown_key_reads_as_the_key() -> None:
    assert ui_text("errors.noSuchKey") == "errors.noSuchKey"


def test_the_active_language_is_used() -> None:
    english = ui_text("settings.close")

    set_ui_language("de")

    assert ui_text("settings.close") == _strings("de")["settings.close"] != english


def test_an_unknown_language_falls_back_to_english() -> None:
    set_ui_language("xx")

    assert ui_text("settings.close") == _strings("en")["settings.close"]


@pytest.mark.parametrize("language", _LANGUAGES)
def test_every_english_key_is_translated(language: str) -> None:
    missing = sorted(set(_strings("en")) - set(_strings(language)))

    assert not missing, f"{language}.json lacks {missing}"


@pytest.mark.parametrize("language", _LANGUAGES)
def test_translations_keep_the_english_placeholders(language: str) -> None:
    english = _strings("en")
    wrong = {
        key: text
        for key, text in _strings(language).items()
        if key in english and placeholders(text) != placeholders(english[key])
    }

    assert not wrong, f"{language}.json placeholders differ from en.json: {wrong}"
