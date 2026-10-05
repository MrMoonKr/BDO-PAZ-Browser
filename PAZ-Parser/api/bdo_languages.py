"""The 13 languages the game ships text in, and which of them the app's UI speaks.

One `language` setting picks both the UI text (`ui/lang/<code>.json`) and the
LOC file the tables read their names from (`ads/<loc_file>` next to the PAZ
folder). A client ships only the LOC files of its region, so a language can
have a UI here while its LOC file is missing; the tables then show the Korean
text stored in them, and the app warns once (`missing_loc_file()`).

`pa_type` is the game's own code, from the `LanguageType` enum in
`luacscript/x64/include/global_define_cpp_enum.luac` (`PA_LT_<pa_type>`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Next to the PAZ folder: <client>/ads/languagedata_en.loc
LOC_FOLDER = "ads"


@dataclass(frozen=True)
class GameLanguage:
    code: str  # The `language` setting and the `ui/lang/<code>.json` file.
    pa_type: str
    name: str  # In the language itself, as the settings list shows it.
    # The LOC file in `LOC_FOLDER`; None for Korean, whose text is in the
    # tables, and for languages whose file name is not confirmed yet.
    loc_file: str | None
    has_ui: bool  # A translated `ui/lang/<code>.json` ships with the app.

    @property
    def text_in_tables(self) -> bool:
        """Korean is the tables' own text, so it never needs a LOC file."""
        return self.pa_type == "KR"


# In the order of the in-game language list. LOC names are confirmed from a
# client or from the region's CDN index (`/UploadData/ads_files`, checked
# 2026-10-06: SA lists pt, JP jp, TW tw, TR tr). Thai, Indonesian and
# Simplified Chinese have no live CDN host to confirm theirs.
GAME_LANGUAGES: tuple[GameLanguage, ...] = (
    GameLanguage("en", "EN", "English", "languagedata_en.loc", has_ui=True),
    GameLanguage("de", "DE", "Deutsch", "languagedata_de.loc", has_ui=True),
    GameLanguage("fr", "FR", "Français", "languagedata_fr.loc", has_ui=True),
    GameLanguage("sp", "ES", "Español", "languagedata_sp.loc", has_ui=True),
    GameLanguage("pt", "PT", "Português", "languagedata_pt.loc", has_ui=False),
    GameLanguage("ru", "RU", "Русский", "languagedata_ru.loc", has_ui=True),
    GameLanguage("tr", "TR", "Türkçe", "languagedata_tr.loc", has_ui=False),
    GameLanguage("kr", "KR", "한국어", None, has_ui=True),
    GameLanguage("jp", "JP", "日本語", "languagedata_jp.loc", has_ui=False),
    GameLanguage("th", "TH", "ไทย", None, has_ui=False),
    GameLanguage("id", "ID", "Bahasa Indonesia", None, has_ui=False),
    GameLanguage("cn", "CH", "简体中文", None, has_ui=False),
    GameLanguage("tw", "TW", "繁體中文", "languagedata_tw.loc", has_ui=False),
)

_BY_CODE: dict[str, GameLanguage] = {language.code: language for language in GAME_LANGUAGES}

UI_LANGUAGES: tuple[GameLanguage, ...] = tuple(language for language in GAME_LANGUAGES if language.has_ui)
UI_LANGUAGE_CODES: frozenset[str] = frozenset(language.code for language in UI_LANGUAGES)


def game_language(code: str) -> GameLanguage | None:
    return _BY_CODE.get(code)


def loc_path(paz_root: Path, code: str) -> Path | None:
    """Where the LOC file of `code` sits for this client, or None when it has none to read."""
    language = _BY_CODE.get(code)
    if language is None or language.loc_file is None:
        return None
    return paz_root.parent / LOC_FOLDER / language.loc_file


def missing_loc_file(paz_root: Path, code: str) -> str | None:
    """The LOC file name `code` needs that this client lacks, else None.

    None too for Korean, which needs none, and for a language whose file name
    is not confirmed: there is nothing to name in a warning.
    """
    path = loc_path(paz_root, code)
    return None if path is None or path.is_file() else path.name
