"""Handler string tables: the loader's English fallback, and every shipped
translation matching its handler's en.json."""
from __future__ import annotations

import json
from pathlib import Path

from _common.lang import handler_text, load_handler_strings
from api.bdo_languages import UI_LANGUAGE_CODES

from tests.lang_files import flat_strings, placeholders

_HANDLERS_DIR = Path(__file__).parent.parent / "handlers"
_TRANSLATIONS = sorted(
    path for path in _HANDLERS_DIR.glob("**/lang/*.json") if path.stem != "en"
)


def _write(path: Path, strings: dict) -> None:
    path.write_text(json.dumps(strings), encoding="utf-8")


def test_a_language_file_overrides_english(tmp_path: Path) -> None:
    _write(tmp_path / "en.json", {"columns": {"id": "ID"}})
    _write(tmp_path / "de.json", {"columns": {"id": "Kennung"}})

    assert load_handler_strings("de", tmp_path)["columns"]["id"] == "Kennung"


def test_keys_a_language_leaves_out_come_from_english(tmp_path: Path) -> None:
    _write(tmp_path / "en.json", {"columns": {"id": "ID", "name": "Name"}, "meta": {"count": "{count} rows"}})
    _write(tmp_path / "de.json", {"columns": {"id": "Kennung"}})

    strings = load_handler_strings("de", tmp_path)

    assert strings["columns"] == {"id": "Kennung", "name": "Name"}
    assert strings["meta"] == {"count": "{count} rows"}


def test_a_language_without_a_file_reads_english(tmp_path: Path) -> None:
    _write(tmp_path / "en.json", {"columns": {"id": "ID"}})

    assert load_handler_strings("fr", tmp_path) == load_handler_strings("en", tmp_path)


def test_a_broken_language_file_reads_english(tmp_path: Path) -> None:
    _write(tmp_path / "en.json", {"columns": {"id": "ID"}})
    (tmp_path / "ru.json").write_text("{ not json", encoding="utf-8")

    assert load_handler_strings("ru", tmp_path) == {"columns": {"id": "ID"}}


def test_a_folder_without_files_reads_empty(tmp_path: Path) -> None:
    assert load_handler_strings("de", tmp_path) == {}


def test_handler_text_fills_counts_with_thousands_separators(tmp_path: Path) -> None:
    _write(tmp_path / "en.json", {"meta": {"count": "{count} rows · {groups} groups"}})

    assert handler_text("en", tmp_path, "meta.count", count=12345, groups=7) == "12,345 rows · 7 groups"


def test_handler_text_reads_the_language(tmp_path: Path) -> None:
    _write(tmp_path / "en.json", {"meta": {"count": "{count} rows"}})
    _write(tmp_path / "de.json", {"meta": {"count": "{count} Zeilen"}})

    assert handler_text("de", tmp_path, "meta.count", count=1000) == "1,000 Zeilen"


def test_handler_text_reads_an_unknown_key_as_the_key(tmp_path: Path) -> None:
    _write(tmp_path / "en.json", {"meta": {}})

    assert handler_text("en", tmp_path, "meta.count", count=1) == "meta.count"


def test_translations_are_named_after_ui_languages() -> None:
    stray = [str(path.relative_to(_HANDLERS_DIR)) for path in _TRANSLATIONS if path.stem not in UI_LANGUAGE_CODES]

    assert not stray, f"no UI language has these codes: {stray}"


def test_translations_cover_exactly_the_english_keys() -> None:
    # A handler is either English only or fully translated in a language.
    problems: dict[str, dict[str, list[str]]] = {}
    for path in _TRANSLATIONS:
        english = set(flat_strings(path.with_name("en.json")))
        translated = set(flat_strings(path))
        missing, extra = sorted(english - translated), sorted(translated - english)
        if missing or extra:
            problems[str(path.relative_to(_HANDLERS_DIR))] = {"missing": missing, "extra": extra}

    assert not problems, problems


def test_translations_keep_the_english_placeholders() -> None:
    wrong: dict[str, list[str]] = {}
    for path in _TRANSLATIONS:
        english = flat_strings(path.with_name("en.json"))
        keys = [
            key
            for key, text in flat_strings(path).items()
            if key in english and placeholders(text) != placeholders(english[key])
        ]
        if keys:
            wrong[str(path.relative_to(_HANDLERS_DIR))] = keys

    assert not wrong, wrong
