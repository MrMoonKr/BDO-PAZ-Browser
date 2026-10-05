# Translating BDO PAZ Browser

## Files

Each language has one JSON file in this folder:

| File | Language |
|------|----------|
| `en.json` | English (source, do not translate) |
| `de.json` | Deutsch |
| `fr.json` | Français |
| `sp.json` | Español |
| `ru.json` | Русский |
| `kr.json` | 한국어 |

## How to translate

1. Open the target language file (e.g. `de.json`).
2. Copy the key structure from `en.json` and replace the English values with your translations.
3. Add your name to the `_meta.authors` array.

Any key you leave out falls back to the English string in the app, so a partial file still works while you translate. The test suite (`tests/test_ui_text.py`) does require every shipped language file to cover every key of `en.json`, with the same `{placeholders}`.

The same files hold the text the Python side builds: error messages (`errors`), the Save dialog filters (`dialogs`), byte units (`units`) and the preview's error boxes and tab labels (`preview`). `ui_text.py` reads them like `t()` does in the page.

## Example

`en.json` (reference):
```json
{
  "toolbar": {
    "openFolder": "📂 Open PAZ Folder"
  }
}
```

`de.json` (partial translation):
```json
{
  "_meta": {
    "language": "Deutsch",
    "code": "de",
    "authors": ["yourname"]
  },
  "toolbar": {
    "openFolder": "📂 PAZ-Ordner öffnen"
  }
}
```

## Rules

- Keep emoji and punctuation that is part of the original string (e.g. `📂`, `⬇`, `✕`).
- Do not translate the `_meta` block keys (`language`, `code`, `authors`, `notes`).
- Do not modify `en.json`, it is the source of truth.
- String values only, do not add new keys that do not exist in `en.json`.
- Keep every `{placeholder}` of the English string; the words around it can move.
- Plural pairs (`matchOne` / `matchMany`, `fileOne` / `fileMany`): if the language has no simple singular and plural, use one wording for both, such as `Совпадений: {count}`.

## Adding UI text (developers)

Never write user-visible text straight into HTML, JS or Python UI code:

- HTML: a `data-i18n`, `data-i18n-title` or `data-i18n-placeholder` attribute with the key.
- JS: `t("section.key", { args })` from `js/core/i18n.js`.
- Python: `ui_text("section.key", name=value)` from `ui_text.py`.

Add the key to `en.json` and translate it in every other file in the same change.
