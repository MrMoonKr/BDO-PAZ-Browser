# Handler Guide

This guide explains how custom preview handlers should be structured, loaded, and registered.

## Loader Rules

The browser loads handlers from the `handlers/` folder at startup.

Only files matching these rules are auto-loaded:

- Must be a `.py` file directly inside `handlers/`
- Must **not** start with `_`
- Each loaded file may register one or more handlers with `register_handler(...)`

Example loaded files:

```text
handlers/
├── dbss_handler.py
├── texture_handler.py
└── model_handler.py
```

Example ignored files/folders:

```text
handlers/
├── _dbss/
├── _common/
├── _helper.py
└── README.md
```

Folders and files starting with `_` are treated as private implementation details.

---

## Recommended Folder Structure

Use one public entry file per format, and keep implementation code in private folders.

```text
handlers/
├── dbss_handler.py                 # Public entry file, auto-loaded
│
├── _dbss/                          # Private DBSS package
│   ├── __init__.py
│   ├── registration.py             # Registers DBSS handlers
│   │
│   ├── common/                     # DBSS-specific helpers
│   │   ├── __init__.py
│   │   ├── binary.py
│   │   ├── html.py
│   │   └── constants.py
│   │
│   ├── titleoffset/
│   │   ├── __init__.py
│   │   └── handler.py
│   │
│   ├── title/
│   │   ├── __init__.py
│   │   └── handler.py
│   │
│   └── titlebuff/
│       ├── __init__.py
│       └── handler.py
│
└── _common/                        # Shared helpers for all formats
    ├── __init__.py
    └── loc.py
```

When adding another format later:

```text
handlers/
├── dbss_handler.py
├── texture_handler.py
├── model_handler.py
│
├── _dbss/
├── _texture/
├── _model/
└── _common/
```

---

## Public Entry File

A public entry file should stay small.

Example:

```python
# handlers/dbss_handler.py

from _dbss.registration import register_dbss_handlers

register_dbss_handlers()
```

The entry file exists so the plugin loader can discover the handler package.

---

## Registration File

Group all registrations for one format in a registration module.

```python
# handlers/_dbss/registration.py

from bdo_preview import register_handler

from .titleoffset.handler import TitleOffsetHandler
from .title.handler import TitleDbssHandler
from .titlebuff.handler import (
    TitleBuffListOffsetHandler,
    TitleBuffListHandler,
)


def register_dbss_handlers() -> None:
    register_handler("titleoffset.dbss", TitleOffsetHandler())
    register_handler("title.dbss", TitleDbssHandler())
    register_handler("titlebufflistoffset.dbss", TitleBuffListOffsetHandler())
    register_handler("titlebufflist.dbss", TitleBuffListHandler())
```

---

## Registration Keys

Handlers can be registered by exact filename or by extension.

```python
register_handler("title.dbss", TitleDbssHandler())
register_handler(".dbss", GenericDbssHandler())
```

Resolution order:

1. Exact filename match
2. Extension fallback
3. Raw hex fallback

Exact filename handlers should be preferred for known formats.

Extension handlers are useful for generic fallback previews.

---

## Handler Template

All parsed-view handlers must implement `get_records()` and `render_records_page()`.

- `get_records()` parses the binary and returns all records as plain dicts (no HTML). The base class caches the result per data object using `_data_cache`, so paging, tab search, and CSV export all reuse the same parse without re-reading the file.
- `render_records_page()` converts one page of records into an HTML fragment.
- `sortable_fields()` opts the table into sorting, see [Sortable Columns](#sortable-columns).

```python
# handlers/_example/myfile/handler.py

from __future__ import annotations

from bdo_models import PazEntry
from bdo_preview import PreviewHandler
from _common.html import Column, e, sort_keys, table


_COLUMNS = [
    Column("ID",   "num", sort_key="id"),
    Column("Name",        sort_key="name"),
]


class MyFileHandler(PreviewHandler):
    def sortable_fields(self) -> frozenset[str]:
        return sort_keys(_COLUMNS)

    def companions(self, entry: PazEntry) -> list[str]:
        folder = entry.internal_path.rsplit("/", 1)[0]
        return [f"{folder}/myindex.dbss"]

    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return [{"id": r.id, "name": r.name} for r in _parse(data)]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        meta = f"{len(records):,} records"
        rows = [[e(r["id"]), e(r["name"])] for r in slice_]
        return table(meta, _COLUMNS, rows)
```

### Sortable Columns

Parsed tables are paged, so the server sorts the full record list and then
renders the requested page. The browser never sorts the rows on screen.

A handler opts in with two pieces:

1. Give each sortable `Column` a `sort_key`: the record field (from
   `get_records()`) the column sorts by. Use the raw value, not the rendered
   text: `duration_ms`, not the `1h 30m` string; `offset`, not `0x0000ABCD`.
2. Return `sort_keys(columns)` from `sortable_fields()`. The API rejects any
   field not in this set.

When the column labels come from the handler's `lang/*.json`, build the list in
a `_columns()` method and use it in both places:

```python
def _columns(self) -> list[Column]:
    cols = load_handler_strings(self.lang, _LANG_DIR).get("columns", {})
    return [
        Column(cols.get("buffId", "Buff ID"), "num", sort_key="buff_id"),
        Column(cols.get("icon", "Icon"), sort_key="icon_path"),
    ]

def sortable_fields(self) -> frozenset[str]:
    return sort_keys(self._columns())
```

Columns without a `sort_key`, and plain `(label, css_class, extra_attrs)`
tuples, render as normal headers you cannot click. A handler that declares no
fields shows no sortable headers at all.

Picking the field behind a column:

- **Derived cells get their own field.** When a cell is built at render time (a
  LOC name with a Korean fallback, a label from a lookup table, an icon path
  resolved from an ID), compute it once in `get_records()`, store it on the
  record and render from that field. The sort and the cell then agree, and the
  logic lives in one place. `title.dbss` stores `title`, `requirement`,
  `category` and `is_special` this way.
- **Columns that come and go stay declared.** A LOC name column that only
  renders with LOC loaded, or flag columns that only render when a flag is set
  somewhere, still belong in `sortable_fields()`. Otherwise a saved sort on
  them is dropped the first time the file opens without them. Build the list
  with a parameter (`_columns(has_loc)`) and declare the full set:
  `sort_keys(self._columns(has_loc=True))`.
- **Fields that are not on the record** (one entry of a list, say) can still
  sort: override `_build_sort_order`, pull the values yourself and pass them to
  `table_sort.sort_order_by_values`. `characterspawntype.dbss` sorts its
  `flag_NN` columns this way from each record's `flags` list, so it does not
  add 44 keys to every one of its 24,017 records.
- **Leave list columns unsortable** (quest titles, page titles, value lists).
  They would sort by their string form, which is rarely useful.
- **Store "none" as `None`, not `0`.** When a field uses `0` for "no linked
  item" or "no next tier" and the cell shows a dash, set it to `None` in
  `get_records()` (`record["item_id"] = record["item_id"] or None`). A `0`
  would sort first ascending even though the cell looks empty; `None` sorts
  last both ways and exports as an empty CSV cell. Keep the parser returning
  the raw `0` and convert only in the handler.

Ordering rules (`table_sort.py`):

- Numbers sort before text, and text ignores case. Anything else (lists,
  tuples) sorts by its string form.
- Empty values (`None`, blank strings, empty lists, NaN) go last in both
  directions.
- The sort is stable, so equal values keep their file order.

Clicking a new column sorts it ascending. Clicking the active column flips the
direction. Both jump to page 1, and paging keeps the sort. While the sorted
page loads, the clicked header shows a spinner, the rows fade (after 120 ms, so
fast sorts do not flicker) and headers ignore further clicks. This needs no
handler code. Each file's sort is
saved in `paz_config.json` under `table_sort`, keyed by file name and storing
the field key (`{"buff.dbss": {"field": "duration_ms", "dir": "desc"}}`). The
file reopens sorted. If the handler no longer declares that field, the entry is
dropped and the file opens unsorted.

The sorted order is cached per field and direction for each loaded file, as a
compact `array("I")` of record indices. Tab search reports its matches as
positions in the sorted view. Changing the sort re-runs an active search
without leaving page 1: the first match is highlighted when it is on that page,
otherwise the counter shows the total and Enter jumps to it. CSV export ignores the sort and writes
`get_records()` in file order, the cheapest path.

Ordering rules have fast paths for all-integer and all-text columns, which
matter at a million rows. Mixed columns fall back to a slower per-row key.

#### Sorting a Page-at-a-Time Handler

By default a sort goes through `get_records()`, which materialises every
record. That is fine for tens of thousands of rows. A handler that overrides
`render_data_page()` to avoid a full parse should override two more methods,
so sorting reads its index instead:

- `_build_sort_order(data, entry, companions, sort)` returns the record
  indices in sorted order. Pull one raw value per record from the index and
  pass them to `table_sort.sort_order_by_values(values, sort.descending)`.
- `render_sorted_page(data, entry, companions, page, page_size, sort)` slices
  `self.sorted_order(...)` for the page and builds only those records.

`handlers/loc_handler.py` is the reference: 1.38 million strings, where a
numeric column sorts in about 0.25 s and the text column in about 1.3 s, then
each page renders in a few milliseconds. If a table renders its own HTML instead of
`table()`, emit its headers with `header_cell(column)` so they carry the
`sortable` class and `data-sort-key`.

`handlers/_dbss/quest/handler.py` does the same over its record index.
Its records carry scripts thousands of characters long, so `_build_sort_order`
parses one row at a time and keeps only the sorted field. Every column sorts in
about 0.5 s on the 19,599-quest fixture, on top of the 0.35 s walk that builds
the index on open.

---

## Unit Tests

Every parsed handler should have a handler-local pytest file named `test_handler.py`.
Place it beside the handler implementation so the format contract stays close to the
code that parses it.

Example:

```text
PAZ-Parser/
├── tests/
│   ├── framework.py          # public re-export for test helpers
│   ├── specs.py              # DeclaredCountTest, TargetTest, SchemaTest, RangeTest
│   ├── declared.py           # header_count(), fixed_rows(): counts read from the input
│   ├── case_input.py         # CaseInput: the data file and companion bytes a case parsed
│   ├── models.py             # HandlerCase, HandlerResult
│   ├── runner.py             # run_case(), load_case()
│   ├── fixtures.py           # auto-fetches test inputs
│   ├── fixture_sync.py       # refreshes fixtures when the client changes
│   └── fixtures/             # gitignored cached binaries
└── handlers/
    └── _dbss/
        └── title/
            ├── handler.py
            └── test_handler.py
```

`HandlerCase` describes one handler input and its assertions:

```python
from tests.framework import DeclaredCountTest, HandlerCase, TargetTest, case_id, header_count

CASE = HandlerCase(
    handler_name="title.dbss",
    data_file="title.dbss",
    companion_files={"titleoffset.dbss": "titleoffset.dbss"},
    loc_file="languagedata_en.loc",
    uses_loc=True,
    loc_fields=["Title", "TitleRequirements"],
    internal_path="gamecommondata/binary/title.dbss",
    tests=[
        DeclaredCountTest(declared=header_count(offset=0, companion="titleoffset.dbss")),
        TargetTest(col="TitleId", value=3, expected={"TitleId": 3}),
    ],
)


@pytest.mark.parametrize("spec", CASE.tests, ids=case_id)
def test_title_dbss(spec, title_result):
    title_result.check(spec)
```

Available specs:

| Spec | Purpose |
|---|---|
| `DeclaredCountTest` | Checks the parsed row count against the count the input declares. |
| `TargetTest` | Finds records by column value and checks one or more expected rows. |
| `SchemaTest` | Checks required keys exist on every row. |
| `RangeTest` | Checks every value in one column is within a min/max range. `None` (an empty cell) is skipped. |

`HandlerResult.check(spec)` runs a spec against the parsed records and the input
bytes (`CaseInput`: the data file and its companions by basename). Only
`DeclaredCountTest` reads the bytes: its `declared` callable takes the `CaseInput`
and returns the count the file states about itself. `tests.framework` has two
builders, `header_count(offset, fmt="<I", companion=None)` for a count field and
`fixed_rows(row_size, header_size=0, companion=None)` for a table of fixed rows
that must fill the file exactly. A format whose count needs more (a grouped
offset table, a count spread over blocks) defines its own callable in its test
module, like `_offset_rows` in `journalquest/test_handler.py`. Derive it from
headers and sizes, not by repeating the parser's walk.

Expected dictionaries use subset matching. Tests only check declared keys, so adding
new fields to a handler does not break existing tests.

A handler that reads a [lookup index](#lookup-indexes) sees none in a test
unless the case installs it: `lookup_indexes={IndexKind.CHARACTER_ITEM: {2053:
58011}}`. Install only the links the `TargetTest`s check, since the real index
comes from another table; test the builder itself against that table's fixture
(see `test_knowledge_index_holds_every_granting_character` in
`characterstatic/test_handler.py`).

### Tests Must Survive a Game Update

A test fails only when the parser is wrong, never because a patch added,
removed or rebalanced content. The fixtures are cached copies of the installed
client and get refreshed when it is patched (see below), and a patch changes
counts, file order and balance values while the layout stays the same. So assert what stays true:

- **Structure and invariants.** Every record parses, the walk ends exactly at
  the end of the file or at the offset table's last byte, the row count equals
  the count the file or its offset table declares, keys repeat where the
  format repeats them. Derive expected counts from the data, never write the
  current number.
- **Schemas and value domains.** `SchemaTest` for required keys, `RangeTest`
  for enums and bounded fields (`quest_category` in `0`-`19`, flags `0`/`1`).
- **Identity anchors.** `TargetTest` by a stable key on identity fields that a
  patch does not touch: node `1` is Velia, class type `25` is Kunoichi, packed
  quest ID `1050655` splits into chain `2079` / quest `16`, an icon path's
  folder. Look records up by key, not by position.

Avoid:

- Literal row counts: new content changes them. Use `DeclaredCountTest`.
- Record positions (`records[0]`, the last row): inserted records shift every
  later row. Use a keyed `TargetTest` instead.
- Balance values: favor, interest, prices, stats, rewards and costs are
  retuned by patches. Assert their type or range, not the number.
- Totals and "N of M" counts from the current client; put those in the
  format doc as observations, dated, where a patch can make them stale.

Check a converted test against freshly extracted fixtures as well as the
frozen ones: point `PAZ_PARSER_FIXTURES_DIR` at an empty folder and the run
fetches every fixture from the configured client. English LOC text changes too
(journal book titles were renamed between clients), so keep a LOC-text
assertion only if it holds on both.

If `get_records()` returns raw snake_case fields but the test should assert the
user-facing table contract, add a `record_mapper` to `HandlerCase`. The mapper
receives one raw record and returns the normalized dictionary used by test specs.

`tests/test_handler_sort.py` needs no per-handler code. It collects every
`HandlerCase` in the handler-local test modules, renders page 1 and checks that
each `data-sort-key` header is in `sortable_fields()`, then sorts by every
declared field in both directions. A handler that renders no sortable headers,
or crashes while rendering or sorting, fails there. Parsed LOC is kept per
fixture and restored between cases, so the whole sweep takes about 25 s.

Fixtures are input files required by tests. Do not commit extracted game files.
`PAZ-Parser/tests/fixtures/` is gitignored except for `.gitkeep`. Missing fixtures
are fetched automatically:

- PAZ files are extracted with `browser.py --file <name> --output PAZ-Parser/tests/fixtures`.
- External files such as `languagedata_en.loc` are copied from the configured game folder.

The cached fixtures follow the installed client. `.client_stamp.json` in the
fixtures folder records which client they came from: the `.meta` header
version and size, plus the size and modified time of `languagedata_en.loc`
(it sits outside the PAZ folder, so the meta version does not cover it). At
the start of every run the stamp is compared with the installed client, and
when they differ every cached fixture is fetched again before any test runs:

```text
fixtures: refreshing 74 files (client 3457 -> client 3458)
fixtures: up to date with client 3458
```

Each file is fetched into a staging folder and then replaces the cached copy,
and the stamp is written only after every fetch succeeded. A failed fetch
stops the run and keeps the old files and stamp, so the next run retries.
Without a configured or reachable client the run uses the cached fixtures as
they are and says so.

| Option                | Effect                                                          |
|-----------------------|-----------------------------------------------------------------|
| (none)                | Refresh only when the installed client changed                  |
| `--refresh-fixtures`  | Fetch every cached fixture again, even from the same client     |
| `--frozen-fixtures`   | Skip the client check, use the cached files (compare snapshots) |

Do not re-pin expected values to make a refreshed run pass; a failure after a
refresh means the parser or the test assumed something a patch can change.

The app must have a saved PAZ folder in `PAZ-Parser/paz_config.json`. Open a PAZ
folder once in the GUI if test fixture fetching fails.

Run all unit tests with:

```bash
python -m pytest -v -s
```

Pytest expands each spec into a separate test item and parses each handler once:

Use `case_id` from `tests.framework` for `pytest.mark.parametrize(..., ids=case_id)`
so test output names stay readable instead of pytest's default `spec0`, `spec1`, `spec2`.

| Spec type           | ID format                               | Example                  |
|---------------------|-----------------------------------------|--------------------------|
| `DeclaredCountTest` | `declared row count`                    | `declared row count`     |
| `SchemaTest`        | `schema: {key1}, {key2}, ...`           | `schema: id, name, kind` |
| `RangeTest`         | `{col} in [{min}, {max}]`               | `kind in [1, 13]`        |
| `TargetTest`        | `{col} = {value}`                       | `TitleId = 3`            |
| `TargetTest`        | `{col} in {a}-{b}` (2-value collection) | `slot in 0-19598`        |
| `TargetTest`        | `{col} in {v1}, {v2}, ...` (3+)         | `kind in 1, 2, 5`        |

```text
title.dbss
  rows:   3,048
  parse:  64 ms
  loc:    0 misses / 6,096 lookups

PAZ-Parser/handlers/_dbss/title/test_handler.py::test_title_dbss[declared row count] PASSED
PAZ-Parser/handlers/_dbss/title/test_handler.py::test_title_dbss[TitleId = 3] PASSED
```

---

## Lazy Parsed Handlers

All handlers are lazy by default. The base class caches the result of `get_records()`
per data object, so paging, search, and record count never re-parse the same file.
No opt-in is required: implement `get_records()` and `render_records_page()` and the
rest is handled automatically.

### Building a Parsed Index

For formats that build a heavy internal structure (an offset table, a packed index,
etc.), use `_data_cache()` to build it once per data object:

```python
class MyFormatHandler(PreviewHandler):

    def _get_index(self, data: bytes) -> MyIndex:
        # Build once; rebuild only when data object identity changes.
        return self._data_cache(data, "index", lambda: build_index(data))

    def get_record_count(self, data, entry, companions) -> int:
        return self._get_index(data).count

    def render_data_page(self, data, entry, companions, page, page_size) -> str:
        # Parse only the needed page, avoid materialising all records first.
        records = self._get_index(data).records_for_page(page, page_size)
        return _render_table(records, page, page_size)

    def search_records(self, data, entry, companions, query) -> list[int]:
        return self._get_index(data).search(query)

    def get_records(self, data, entry, companions) -> list[dict]:
        # Compatibility fallback for CSV export and test assertions.
        return self._get_index(data).all_records()
```

`_data_cache(data, name, build_fn)` supports multiple named slots per handler instance
and rebuilds automatically when a different file is selected. Use a descriptive name
(`"index"`, `"offset_table"`) so slots do not collide if the handler caches more than one
structure.

### When to Override `render_data_page`

Override `render_data_page()` only when the format supports **parsing a single page
without reading all records first**, for example a format with a stored offset table
that lets you seek directly to each record.

If `get_records()` is fast (small file, trivial parse), the base implementation is
sufficient: it calls `get_records()` once, caches the result, and slices it per page.

---

## Streamed Preview Handlers

Large browser-native previews should subclass `StreamPreviewHandler` instead of
reading the full payload into HTML.

Use streamed handlers for formats that can preview from a local URL, such as
video or audio. The API supplies a tokenized localhost URL and skips the eager
`read_entry_payload(...)` call during initial selection.

```python
from bdo_models import PazEntry
from bdo_preview import StreamPreviewHandler, register_handler


class MyVideoHandler(StreamPreviewHandler):
    mime_type = "video/webm"

    def render_stream(self, stream_url: str, entry: PazEntry) -> str:
        return (
            '<div class="video-view">'
            f'<video controls preload="metadata" src="{stream_url}"></video>'
            '</div>'
        )


register_handler(".webm", MyVideoHandler())
```

Rules:

- `mime_type` should match the streamed content type.
- `render_stream()` returns only the preview shell HTML.
- Do not base64-encode the payload inside the handler.
- The stream endpoint supports browser `Range` requests, but the current backend still decodes the full entry before slicing the response.

---

## Companion Files

Override `companions()` when a handler needs related files.

```python
def companions(self, entry: PazEntry) -> list[str]:
    folder = entry.internal_path.rsplit("/", 1)[0]

    return [
        f"{folder}/titleoffset.dbss",
        f"{folder}/languagedata_en.loc",
    ]
```

Companion files are passed into `get_records()` as:

```python
companions: dict[str, bytes]
```

The dictionary is keyed by basename.

Example:

```python
offset_raw = companions.get("titleoffset.dbss")
loc_raw = companions.get("languagedata_en.loc")
```

Disk files pre-loaded by the browser may also be merged into `companions`.

For example:

```python
companions.get("languagedata_en.loc")
```

---

## HTML Output Rules

Handlers return HTML fragments.

Always escape user-visible or file-derived values.

Good:

```python
import html

return f"<div>{html.escape(name)}</div>"
```

Avoid:

```python
return f"<div>{name}</div>"
```

Use shared HTML helpers when available.

Example:

```python
from _common.html import error, icon_cell, table
```

Use `icon_cell(path)` for icon path columns so DBSS/BSS table previews keep
consistent spacing and escaping. The frontend lazy-loads matching PAZ image
entries into those cells, while parsed CSV export keeps the raw icon path field.

---

## Raw Hex Preview

Handlers should only render their parsed preview.

The main preview UI is responsible for switching between:

- Parsed preview
- Raw hex preview

Do not manually include raw hex tabs inside individual handlers.

This keeps all handlers consistent.

---

## Shared Helpers

Use `_common/` for helpers shared by multiple formats.

Examples:

```text
_common/
├── loc.py
├── binary.py
├── html.py
├── pabr_offset.py       # u16-keyed offset companions, with or without PABR magic
└── prefixed_string.py   # length-prefixed strings: strict and lenient readers
```

Read an offset companion with `parse_pabr_offset_rows()` (PABR magic, count,
rows) or `parse_bare_offset_rows()` (count, rows), never by hand. For inline
strings, `read_prefixed_at()` reads a prefix at a known position and returns
the next one; `read_prefixed_utf16()` and `find_prefixed_ascii()` are for text
whose position is only a guess.

Use format-specific helpers inside that format package.

Examples:

```text
_dbss/common/
├── binary.py
├── constants.py
└── html.py
```

Rule of thumb:

- Used by only DBSS → `_dbss/common/`
- Used by multiple formats → `_common/`

---

## Lookup Indexes

Some joins need a table far too large to open as a companion on every preview,
such as the 194 MB `itemenchant.dbss`. For those the app keeps **lookup
indexes**: cached `entity ID -> value` tables built once per PAZ folder and
injected into `_common/lookup_index.py`, the same way `init_loc()` supplies LOC
data. A handler reads one by kind and ID:

```python
from _common.lookup_index import IndexKind, lookup

item_id = lookup(IndexKind.CHARACTER_ITEM, character_id)  # None when missing
```

`lookup()` returns `None` both when the index is not loaded and when it has no
entry for the ID; render a dash in either case. `is_index_loaded()` tells the
two apart when it matters. Unit tests install an index with
`init_index(kind, mapping)` and drop it with `clear_indexes()`; a
`HandlerCase` takes `lookup_indexes={kind: mapping}`, which the runner installs
while the handler runs and removes afterwards.

Every index is one `IndexSpec(kind, sources, build)` in
`INDEX_SPECS` (`api/bdo_lookup_indexes.py`). `build` receives the payloads of
`sources` as positional arguments, in the order listed, and returns
`{entity_id: value}`. `build_indexes()` reads each source once, so specs that
share a table reuse its payload; a spec with a missing source is skipped. Adding
an index is one `IndexKind` member plus one spec.

`Api._load_lookup_indexes()` installs every index at folder load. Results are
cached by `paz/bdo_index_cache.py` in `paz_browser_indexes.cache` next to the
PAZ files, keyed by `IndexKind.value` (renaming a value orphans its cached data
until the rebuild) and invalidated on the PAZ meta version or when the code that
builds them changes. The cache stores `builder_fingerprint()`, a hash of
`api/bdo_lookup_indexes.py` plus every project module it imports, so editing a
builder or a helper such as `_common/prefixed_string.py` rebuilds the indexes on
the next launch. Keep the builder imports at the top of that module: a lazy
import would hide the builder from the fingerprint.

Values are pickled, so an index may hold icon paths, linked IDs or tuples of
IDs (`LookupValue`).

| Kind             | Sources                                    | Value          |
| ---------------- | ------------------------------------------ | -------------- |
| `ITEM_ICON`      | `itemenchant.dbss`, `itemenchantoffset.dbss` | icon path    |
| `QUEST_ICON`     | `quest.dbss`, `allquestlist.bss` (record order) | icon path |
| `CHARACTER_ICON` | `characterobject.dbss`, `characterobjectoffset.dbss` | icon path |
| `CHARACTER_ITEM` | `itemenchant.dbss`, `itemenchantoffset.dbss` | item ID      |
| `KNOWLEDGE_CHARACTERS` | `characterstatic.dbss`, `characterstaticoffset.dbss` | character IDs (tuple) |

`CHARACTER_ITEM` maps a character to the one base item that places or summons
it (`character_id` at `+0xAA` in
[itemenchant.dbss](file-formats/itemenchant_dbss.md)); characters named by zero
or several items are left out. The `characterobject.dbss` Item column reads it.

`KNOWLEDGE_CHARACTERS` maps a knowledge card to every character whose
`getknowledge(<id>);` action script grants it, in ascending ID order. The
`mentalcard.dbss` Learned From column reads it.

---

## Icons

`icon_cell(path)` renders an icon cell. The path is not fetched at parse time,
the UI lazily resolves it against the PAZ entry map when the cell scrolls into
view, so a handler only has to emit a correct path string.

Icons are looked up by **kind and entity ID** through `_common/icon_index.py`,
never by hand-written template:

```python
from _common.icon_index import IconKind, icon_path

row["icon_path"] = icon_path(IconKind.ITEM, item_id)
```

`icon_path()` tries two sources in order:

1. **The lookup index for that kind**, named by `ICON_INDEXES`
   (`IconKind.ITEM` reads `IndexKind.ITEM_ICON`, and so on). For items it is
   built from the level-0 records of `itemenchant.dbss`, which store each item's
   icon path inline.
2. **Derivation from the ID**, when that kind declares one and the index has no
   entry. `IconKind.ITEM` derives into the flat `product_icon_png` folder.

Kinds are an `Enum` so a typo is a failure at import rather than a silently
empty icon column. Adding one means adding the member, its optional deriver in
`_DERIVERS`, and, when a table stores its icons, an `IndexKind` with its spec
(see [Lookup Indexes](#lookup-indexes)) mapped in `ICON_INDEXES`.

`CHARACTER` has one extra step. After every index is built,
`build_indexes()` gives each character without a working icon the icon of the
item that places or summons it, through `CHARACTER_ITEM` and `borrow_icons()`.
A working own icon always wins, and a borrowed icon is used only when its file
exists. The cached `CHARACTER_ICON` index already holds the borrowed icons.

| Kind                | Source                  | Entries (client 3458) | Derivation fallback |
| ------------------- | ----------------------- | ------- | ------------------------- |
| `ITEM`              | `itemenchant.dbss`      | 70,284  | `product_icon_png`        |
| `QUEST`             | `quest.dbss`            | 19,324  | none                      |
| `CHARACTER`         | `characterobject.dbss`, gaps from `itemenchant.dbss` | 6,165 | none |
| `PET_EQUIP_SKILL`   | none                    | 0       | `08_servant_skill/02_pet` |
| `FAIRY_EQUIP_SKILL` | none                    | 0       | `08_servant_skill/02_pet` |

### Fixing an icon by hand

`icon_path()` checks three tiers in order: **override, index, derivation.**

Overrides live in `_common/icon_overrides.json`, keyed by `IconKind.value` then
entity ID. They are repo data, not PAZ data, so they survive every index rebuild
and every game patch:

```json
{
  "item": { "222": "ui_texture/icon/new_icon/03_etc/00000222.dds" },
  "quest": {},
  "character": {}
}
```

An empty string means "this entity genuinely has no icon", which suppresses a
wrong derived guess rather than replacing it. A malformed file is reported by
`icon_override_error()` and ignored rather than crashing the app, so check that
helper if an override does not take effect.

Overrides are the intended fix for the ~535 IDs whose source table references an
icon the client does not ship. Those references do not change between patches,
so a correction made once keeps working.

When a referenced icon is not in the PAZ, the cell collapses to a dash rather
than leaving an empty swatch beside a path that resolves to nothing. The full
path stays in the cell's `title` attribute, so it is still there on hover. That
covers the roughly 535 IDs whose source table points at an icon the client does
not ship, until an override supplies the right path.

How far each index actually reaches differs a lot, so check before assuming an
icon column will look populated. Measured against the live PAZ:

| Kind        | IDs that exist | Resolve to a real file |
| ----------- | -------------- | ---------------------- |
| `ITEM`      | 73,790         | 93.8%                  |
| `QUEST`     | 19,486         | 83.9%                  |
| `CHARACTER` | 24,418         | 24.9%                  |

`CHARACTER` is low because only placeable world objects (mostly house
furniture) and the characters an item places or summons (fences, crops, pets)
have an icon, 6,068 of 24,418 IDs. NPCs and monsters have none. That is expected
rather than broken, but it means a character icon column is mostly empty.

The two equip-skill kinds are derivation only: no table stores their paths, but
routing them through the registry keeps every icon template in one module and
lets `icon_overrides.json` correct them like any other kind. Quest and character icons are named after
assets far more often than after their ID, so a guess would be wrong more often
than right; those kinds return an empty path and the cell renders a placeholder.

The index matters because most item icons are not reachable from the ID. Of
~77,000 files under `ui_texture/icon`, the ID-named ones live in dozens of
per-category folders, and thousands more are named after a 3D asset
(`inhouse_cultivate_sea_clam_01_wall.dds`) with no numeric component at all.

| Item set                     | Derived from ID | With the index |
| ---------------------------- | --------------- | -------------- |
| All LOC type 0 IDs           | 14.9%           | 93.7%          |
| `npcgift.dbss` gift items    | 90%             | 100%           |

Cash-shop product icons are deliberately excluded. `cashproduct.dbss` links a
product to the item it grants, but its icon is the shop product art, not the
item's icon: item 1 (Silver) maps to `loyalties.dds`, the product that grants
it. Its icons differ from the item's own in every overlapping case, and it adds
no items that `itemenchant.dbss` does not already cover.

Handlers that read an icon path stored in their own records, such as `pet.dbss`,
`petaction.dbss`, `quest.dbss`, `plantworker.bss`, `itemenchant.dbss` and
`cashproduct.dbss`, keep using that path directly. It is already authoritative,
and for `itemenchant` and `quest` the index is built from it, so routing those
through `icon_path()` would be circular.

---

## Localization

The app's active language code (`"en"`, `"de"`, `"fr"`, `"sp"`, `"ru"`, `"kr"`) is
available to every handler via `self.lang`. It is set automatically before any handler
method is called and updated whenever the user changes language in Settings.

Use it in `get_records()` to return language-appropriate display strings:

```python
_LABELS = {
    "en": {"active": "Active", "inactive": "Inactive"},
    "de": {"active": "Aktiv",  "inactive": "Inaktiv"},
    "kr": {"active": "활성",    "inactive": "비활성"},
}

class MyHandler(PreviewHandler):
    def get_records(self, data, entry, companions):
        labels = _LABELS.get(self.lang, _LABELS["en"])
        return [
            {"id": r.id, "status": labels["active"] if r.active else labels["inactive"]}
            for r in _parse(data)
        ]
```

For larger string sets, ship JSON files next to the handler and use the shared helper:

```python
from pathlib import Path
from _common.lang import load_handler_strings

_LANG_DIR = Path(__file__).parent / "lang"

class MyHandler(PreviewHandler):
    def get_records(self, data, entry, companions):
        s = load_handler_strings(self.lang, _LANG_DIR)
        ...
```

`load_handler_strings(lang, strings_dir)` tries `{strings_dir}/{lang}.json` then falls
back to `{strings_dir}/en.json`. Returns `{}` if neither file exists.

**Example `lang/en.json`** for a handler that displays category names and column headers:

```json
{
  "columns": {
    "id":       "Title ID",
    "category": "Category",
    "title":    "Title",
    "effect":   "Effect"
  },
  "category": {
    "0": "World",
    "1": "Combat",
    "2": "Life Skill",
    "3": "Fishing"
  }
}
```

A partial translation file (`lang/de.json`) only needs to cover the keys it changes:

```json
{
  "category": {
    "0": "Welt",
    "1": "Kampf",
    "2": "Lebensfertigkeiten",
    "3": "Angeln"
  }
}
```

Missing keys are not resolved automatically by `load_handler_strings`. If you ship
partial files, do the merge yourself:

```python
import json
from pathlib import Path
from _common.lang import load_handler_strings

_LANG_DIR = Path(__file__).parent / "lang"

def _strings(lang: str) -> dict:
    if lang == "en":
        return load_handler_strings("en", _LANG_DIR)
    base = load_handler_strings("en", _LANG_DIR)
    override = load_handler_strings(lang, _LANG_DIR)
    # shallow-merge each top-level section
    return {k: {**base.get(k, {}), **override.get(k, {})} for k in base}
```

For most handlers a flat single-language file is simpler, so only bother with partial
merging when the string table is large enough that translators would realistically
only cover part of it.

Rules:
- Always provide English (`"en"`) as the fallback, since `self.lang` may be a code your
  handler does not yet translate.
- Put translated strings in `get_records()` so they land in `records` dicts, which
  means tab search and CSV export also see the localized values.
- Do not put translated labels directly in `render_records_page()`, because the HTML layer
  should be format-agnostic.

---

## Import Rules

From a root handler:

```python
from _dbss.registration import register_dbss_handlers
```

From inside a format package:

```python
from _common.binary import u32
from _common.loc import parse_loc_entries
```

Avoid deep cross-format imports like:

```python
from _texture.some_internal_file import ...
```

If something is shared across formats, move it to `_common/`.

---

## Required `__init__.py`

Every package folder should contain `__init__.py`.

Example:

```text
_dbss/
├── __init__.py
├── common/
│   └── __init__.py
└── title/
    └── __init__.py
```

This keeps imports predictable when handlers are loaded dynamically.

---

## Loader Requirement

The plugin loader should add `handlers/` to `sys.path` before importing plugins.

```python
handlers_path = str(handlers_dir.resolve())

if handlers_path not in sys.path:
    sys.path.insert(0, handlers_path)
```

Without this, imports like this may fail:

```python
from _dbss.registration import register_dbss_handlers
```

---

## Naming Conventions

Use clear names:

```text
handler.py
registration.py
binary.py
html.py
constants.py
```

Use one handler class per preview type when practical.

Good:

```python
class TitleDbssHandler(PreviewHandler):
    ...
```

Avoid vague names:

```python
class Handler(PreviewHandler):
    ...
```

---

## Error Handling

Return a visible error fragment for expected missing data.

```python
return '<div class="error">titleoffset.dbss companion not found.</div>'
```

Do not raise for normal missing companion files.

Raise only for actual programming errors.

---

## Checklist for a New Handler

1. Create a public root file if this is a new format.
2. Create a private implementation folder starting with `_`.
3. Add `__init__.py` to every package folder.
4. Create a `registration.py`.
5. Implement one or more `PreviewHandler` classes with `get_records()` and `render_records_page()`.
6. `get_records()` must return plain dicts, no HTML. Include any LOC-lookup strings here so tab search can find them. Use `self.lang` for language-aware display strings.
7. `render_records_page()` slices `records[page * page_size : ...]` and returns an HTML fragment.
8. Give sortable columns a `sort_key` and return `sort_keys(columns)` from `sortable_fields()` (see [Sortable Columns](#sortable-columns)).
9. Paging and search are lazy by default. For formats with a heavy internal structure, use `_data_cache()` to build the index once and override `render_data_page()` to parse only the requested page.
10. Register by exact filename or extension.
11. Escape all file-derived output (`e()` helper or `html.escape()`).
12. Use `companions()` for related files.
13. Add a handler-local `test_handler.py` with at least count and representative row tests.
14. Keep raw hex switching in the frontend, not the handler.
15. Move reusable logic to `_common/` when another format needs it.

> **Tip:** Press **Ctrl+R** in the GUI to reload all handlers without restarting the app. Changes to any file under `handlers/`, including private packages like `_dbss/`, take effect immediately. If a file is open on the Parsed tab, the preview re-renders automatically.

---

## Minimal New Format Example

```text
handlers/
├── texture_handler.py
└── _texture/
    ├── __init__.py
    ├── registration.py
    └── dds/
        ├── __init__.py
        └── handler.py
```

```python
# handlers/texture_handler.py

from _texture.registration import register_texture_handlers

register_texture_handlers()
```

```python
# handlers/_texture/registration.py

from bdo_preview import register_handler

from .dds.handler import TextureDdsHandler


def register_texture_handlers() -> None:
    register_handler(".dds", TextureDdsHandler())
```

```python
# handlers/_texture/dds/handler.py

from __future__ import annotations

from bdo_models import PazEntry
from bdo_preview import PreviewHandler
from _common.html import e, table

_HEADERS = [("Offset", "num", ""), ("Size", "num", "")]


class TextureDdsHandler(PreviewHandler):
    def get_records(
        self,
        data: bytes,
        entry: PazEntry,
        companions: dict[str, bytes],
    ) -> list[dict]:
        return [{"offset": 0, "size": len(data)}]

    def render_records_page(
        self,
        records: list[dict],
        page: int,
        page_size: int,
    ) -> str:
        start = page * page_size
        slice_ = records[start : start + page_size]
        rows = [[e(r["offset"]), e(r["size"])] for r in slice_]
        return table(f"{len(records):,} records", _HEADERS, rows)
```

This is the simplest possible handler: `get_records()` is called once per file and the base class caches the result automatically. If the format requires a heavy parse (offset table, packed index), see the [Lazy Parsed Handlers](#lazy-parsed-handlers) section and use `_data_cache()` to build the index once.
