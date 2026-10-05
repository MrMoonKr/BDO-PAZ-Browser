# BDO PAZ Browser & Binary Format Tools

> **Work in progress.** Format coverage is incomplete and the API may change. Contributions and corrections are welcome.

A Python tool for browsing, extracting, and previewing files from **Black Desert Online**'s `.paz` game archives, with a plugin system for parsing BDO-specific binary formats.

![BDO PAZ Browser](docs/assets/screenshot.png)

---

## Features

- **GUI browser**, tree-view file explorer for the full PAZ archive, with live search and file preview
- **CLI extraction**, extract files by name or glob pattern without opening the GUI
- **File preview**, text, hex dump, DDS images, and parsed binary tables for known formats
- **Paged preview**, large files (hex and parsed tabs) are paged; navigate with Prev/Next without loading the full DOM
- **Sortable tables**, click a column header to sort the whole parsed table, not just the page on screen; a table opens sorted by its first column, highest first, until you click another sort, which is remembered per file
- **Tab search**, Ctrl+F inline search within hex (byte offset) and parsed (record) tabs; string and hex-pattern modes
- **Export**, save the current file as raw binary (hex tab) or CSV (parsed tab) via the Entry Details panel
- **Game text colours**, LOC text shows the colours of its `<PAColor>` tags, as in game; the **Show game text tags** setting (off by default) also shows the tags themselves
- **Handled tables only**, the **Show only handled tables** setting (off by default) limits the file tree, file search, content search and folder extraction to files with a parsed table view, plus the LOC file
- **Plugin system**, add handlers for new binary formats by dropping a file into `handlers/`
- **Caching**, PAZ index is parsed once and cached; subsequent launches load instantly
- **Parsed table cache**, parsed tables are kept on disk next to the PAZ files, so a big table reopens in a fraction of its parse time (`detail_dialog.dbss` 1.3 s to 0.25 s, `itemenchant.dbss` with its default sort 2.1 s to 0.5 s). The **Parsed Table Cache** setting picks Off, Cache tables when opened (default) or Cache all tables in the background, which parses every table A to Z while the app is idle; the status bar shows the table it is on, how far the pass is, and when it waits for you. A table stays cached across a patch that leaves it, its companions and the LOC text or lookup indexes it reads unchanged. **Delete all caches** in the settings removes the parsed table, icon thumbnail and lookup index caches; the PAZ index cache stays, since rebuilding it takes over a minute

---

## Contributing Format Coverage

BDO has hundreds of undocumented binary formats, contributions and corrections are welcome.

**Reverse engineer a new format**, open a new issue using the [file format template](../../issues/new?template=file-format.yml) and title it `filename.ext` (e.g. `yachtdicepreset.dbss` or `.pac`).

**Improve existing docs**, the format docs in [`docs/file-formats/`](docs/file-formats/) are not all complete. Each doc has an **Open Questions** section listing specific unknowns, if you can answer any of them, feel free to update the doc directly.

**Translate the UI**, UI strings live in [`PAZ-Parser/ui/lang/`](PAZ-Parser/ui/lang/) as small JSON files, one per language. Missing keys fall back to English automatically, so partial translations are fine. See [`TRANSLATING.md`](PAZ-Parser/ui/lang/TRANSLATING.md) for instructions.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for setup, the checks to run before a pull request, and project conventions.

---

## Writing a Preview Handler

Drop a `.py` file (not starting with `_`) into `handlers/`, it is auto-loaded at startup.

All parsed-view handlers must implement two methods:

```python
# handlers/myformat_handler.py
from bdo_preview import PreviewHandler, register_handler
from bdo_models import PazEntry

class MyFormatHandler(PreviewHandler):
    def get_records(self, data: bytes, entry: PazEntry, companions: dict[str, bytes]) -> list[dict]:
        # Parse all records once. Returns plain dicts, no HTML.
        # Cached in memory for paging, tab search, and CSV export.
        return [{"id": r.id, "name": r.name} for r in parse(data)]

    def render_records_page(self, records: list[dict], page: int, page_size: int) -> str:
        # Render one page of records as an HTML fragment.
        start = page * page_size
        slice_ = records[start : start + page_size]
        rows = "".join(f"<tr><td>{r['id']}</td><td>{r['name']}</td></tr>" for r in slice_)
        return f"<table><thead>...</thead><tbody>{rows}</tbody></table>"

register_handler("myfile.dbss", MyFormatHandler())
```

The browser automatically handles:

- Prev/Next page navigation
- Inline tab search (Ctrl+F) across all record field values
- CSV export of the full record list

See [docs/handler.md](docs/handler.md) for the full guide, including companion files, shared helpers, registration patterns, and [adding translations](docs/handler.md#localization).

> **Tip:** Press **Ctrl+R** in the GUI to reload all handlers without restarting the app. If you have a file open on the Parsed tab, the preview re-renders automatically with the updated handler.

---

## Supported Formats

- Handler Supported 32/403 .bss formats.
- Handler Supported 75/374 .dbss formats.
- Handler Supported 24 other formats.

## Documented Formats

See [docs/documented-formats.md](docs/documented-formats.md) for the full table.

---

## Requirements

- Python 3.10+
- [pywebview](https://pywebview.flowrl.com/), GUI shell
- [Pillow](https://python-pillow.org/), optional, for DDS image preview

```
pip install pywebview
pip install pillow        # optional
```

Or install from the provided requirements file:

```
pip install -r PAZ-Parser/requirements.txt
```

---

## Testing

Handler unit tests use pytest and live beside the handler they cover. Missing test inputs are fetched into the gitignored `PAZ-Parser/tests/fixtures/` cache from the configured PAZ folder. When the installed client changes, the next run fetches all of them again (details in `docs/handler.md`).

Install dev dependencies:

```bash
python -m pip install -r PAZ-Parser/requirements-dev.txt
```

Run all unit tests with the full output (a rows / parse time / LOC summary per handler):

```bash
python -m pytest -v -s
```

Or print only failed tests and a pass/total line:

```bash
python -m pytest --clean
```

Open a PAZ folder once in the GUI if fixture fetching has no saved game path yet.

Type-check `PAZ-Parser/`, `browser.py` and `benchmark.py` (from the repo root, so `pyrightconfig.json` applies):

```bash
python -m pyright
```

Run both the tests and pyright before committing a Python change; both should pass with no errors.

---

## Benchmarking

`benchmark.py` times the decode path, and a handler's parse, on fixed input,
so two runs on the same machine can be compared.

```bash
# Time every stage of one entry and save the result
python benchmark.py run --output before.json

# Extract every file of one .paz archive, as extract_all does
python benchmark.py run --archive --repeats 5 --output before.json

# Parse one table with LOC and lookup indexes loaded, as the app does
python benchmark.py run --entry itemenchant.dbss --stages parse --output before.json

# After a change: same command, then compare stage by stage
python benchmark.py run --output after.json
python benchmark.py compare before.json after.json

# Where the time goes: cProfile, top 100 functions by cumulative time
python benchmark.py profile --archive --stages extract --save extract.prof
```

The workload is one entry (`--entry`, default
`morningland_boss_03_02_full.dds`, a 14 MB texture) or one archive
(`--archive`, default `pad05889.paz`, about 800 mixed files). The stages:

| Stage | What it times |
|---|---|
| `decrypt` | ICE decryption of the entry, from memory |
| `decompress` | BDO decompression of the decrypted entry, from memory |
| `read` | The app's path to open a file: disk read, decrypt, decompress |
| `extract` | `extract_all` per file: `read`, then the size check and the write to disk. On an archive, every file in it. The meta file parse is left out: it reads the whole client on every call (over a minute) and would hide the decode time |
| `parse` | The handler's `all_records()` (the cached `get_records()` the app's table uses) on the decoded entry, with its companions, LOC in the language picked in the app and the lookup indexes loaded. Only for a file with a parsed view; LOC and the indexes add about 5 s to start-up, so they only load when this stage runs. Every run parses cold (the handler's cached records and index are dropped first) and runs with the garbage collector on, as in the app, which pauses it while the records are built. The input hash covers the entry only, not its companions or LOC |

To keep numbers comparable, each run:

- **Pins the process to one CPU** (`--cpu`, default 2) at high priority.
  The decode loops are pure Python, so they use one core anyway. Pinning
  stops the OS moving the run between cores; on a hybrid Intel CPU an
  efficiency core runs this code about 1.8x slower, so the benchmark refuses
  one and lists the performance cores. The pin is read back after setting
  it and checked again at the end. `--no-pin` runs unpinned and marks the
  result so. Pinning works on Windows and Linux (Linux without the priority
  raise, which needs root).
- **Keeps the input fixed**: the entry bytes are read into memory once, and
  their SHA-256 is saved so a client patch that changes the file shows up.
- **Warms up first** (`--warmup`, default 1), then times `--repeats` runs
  (default 5) with the garbage collector off, as `timeit` does (`parse`
  keeps it on). What a run returns is freed after the clock stops. The minimum
  is the steadiest figure for CPU-bound code; the median and spread show the
  noise.
- **Saves a fingerprint** with the timings: CPU model, logical CPUs, RAM,
  power plan, OS, Python, git commit, the pinned CPU and the input hash.
  `compare` lists every difference besides the code, so a speedup only
  counts when that list is empty.

`--memory` adds one run per stage under `tracemalloc` for the peak memory.
It traces every allocation, so that run is many times slower and never
shares a run with the timings. `profile` slows every call too; use it to find
hot functions, and `run` for numbers. Its `--save` file opens in snakeviz or
`pstats`.

---

## Usage

### GUI

```bash
python browser.py
```

On first launch, click **Open Folder** and select your BDO PAZ directory (typically `Black Desert/Paz`). The index is parsed and cached, subsequent launches load from cache automatically.

### CLI

```bash
# List files matching a pattern
python browser.py --paz-folder "C:/Games/Black Desert/Paz" --list "title*.dbss"

# Extract files matching a pattern
python browser.py --paz-folder "C:/Games/Black Desert/Paz" --file "title.dbss" --output ./out

# Glob extraction
python browser.py --paz-folder "C:/Games/Black Desert/Paz" --file "*title*" --output ./out

# Parsed records, as the GUI table has them (LOC and lookup indexes loaded)
python browser.py --records buffsimply.bss --where buff_id=48723..48728
python browser.py --records skill.dbss --where buff_ids=48723 --fields skill_no,name,buff_ids --json
python browser.py --records languagedata_en.loc --where "text*=Adventure's Boon" --limit 5

# One parsed page as a standalone HTML file with the app's CSS and icons
python browser.py --render buffsimply.bss --page 2 > page.html

# Lookup indexes: every kind with its size, all entries of one kind, or one ID
python browser.py --index
python browser.py --index knowledge_characters --limit 20
python browser.py --index buff_icon --id 48724
```

If `--paz-folder` is omitted, the CLI reuses the last folder opened in the GUI.
LOC follows the language picked in the GUI settings. Output is UTF-8 whatever
the console code page, and progress messages go to stderr, so redirected
output holds only the result.

`--records <file>` runs the file's handler `get_records()` with its companions,
the rows behind the GUI table and its CSV export. The file is a PAZ path, a
file name, or a pattern that matches one file. Options:

| Option | Meaning |
|---|---|
| `--where field=value` | Equal. Numbers compare as numbers (`0x` hex allowed), text ignores case, `true` / `false` / `yes` / `no` match flags, `none` (or nothing after `=`) matches an empty cell: no value, blank text or an empty list. A list field matches when any item does |
| `--where field=a..b` | Number in the inclusive range; `a..` and `..b` leave one side open |
| `--where field*=text` | Text contains `text`, ignoring case. Text fields are searched as stored, so `*=\n` finds the two-character newline escape |
| `--fields a,b,c` | Only these fields, in this order |
| `--sort field[:desc]` | Sort as the GUI table does (empty values last, text ignoring case, ties in file order), before `--limit` |
| `--json` / `--csv` | Full values as JSON, or CSV like the app's export. The default is an aligned text table; long cells are cut in the middle so both ends stay (a path keeps its file name), and a single row is shown whole |
| `--limit N` | At most N rows, after filtering |
| `--no-loc` | Skip loading LOC (faster; text columns fall back to inline text) |

Several `--where` options must all match. `--index` takes `--json`, `--csv`
and `--limit` too.

The CLI always shows game text tags, whatever the GUI setting: `--render`
draws them next to the colours, and `--records` lists the tagged text in the
fields starting with `_` (`_description_pa` next to the plain `description`).
CSV leaves those fields out, like the app's export.

---

## Project Structure

```
PAZ-Parser/
├── bdo_app.py              # Entry point, GUI launch + CLI argument parsing
├── bdo_models.py           # Data models (shared by all handlers)
├── bdo_preview.py          # Preview handler registry + built-in handlers
├── bdo_server.py           # Local HTTP server for stream preview
├── conftest.py             # pytest setup and handler test summary output
├── record_export.py        # Records as CSV (GUI export and --records --csv)
├── ui_text.py              # UI text for Python-built messages, from ui/lang/*.json
│
├── cli/                    # Command-line commands, one module each
│   ├── session.py          # Loads the PAZ folder headless through Api
│   ├── parsed_file.py      # Resolves a file name to handler, payload, companions
│   ├── files.py            # --list, --file
│   ├── formats.py          # --formats
│   ├── records.py          # --records (record_filter.py, record_output.py)
│   ├── render.py           # --render
│   └── index.py            # --index
│
├── bench/                  # benchmark.py commands (see Benchmarking)
│   ├── cli.py              # run, compare, profile
│   ├── stages.py           # Workloads (one entry, one archive) and their stages
│   ├── timing.py           # Warm-up, timed repeats, optional peak memory
│   ├── pinning.py          # CPU pinning and the performance core check
│   ├── win32.py            # Windows API calls through ctypes
│   ├── machine.py          # Machine fingerprint saved with each result
│   ├── results.py          # Result JSON, read back with every field checked
│   ├── compare.py          # Stage speedups and environment differences
│   ├── profiling.py        # cProfile of one stage
│   └── report.py           # Console tables
│
├── api/                    # pywebview JS API bridge
│   ├── bdo_api.py          # Routing and dispatch
│   ├── bdo_api_helpers.py  # Shared constants and utilities (_norm, _file_icon)
│   ├── bdo_icon_images.py  # Icon thumbnails, the icon popup image and sprite crops
│   ├── bdo_api_preview.py  # Preview assembly and entry loading (PreviewMixin)
│   ├── bdo_api_caches.py   # Parsed table cache modes, Delete all caches (CacheMixin)
│   ├── bdo_records_store.py# Parsed table cache keys and dependency digests
│   ├── bdo_records_prefill.py# Background pass that caches every table
│   └── bdo_api_search.py   # File content search, single-file and cross-file (SearchMixin)
│
├── paz/                    # PAZ archive reading and caching
│   ├── bdo_cache.py        # PAZ index cache
│   ├── bdo_ice.py          # ICE cipher implementation
│   ├── bdo_meta_reader.py  # Meta file reader
│   ├── bdo_payload_cache.py# LRU payload cache
│   ├── bdo_payload_reader.py# Payload decompression + ICE decryption
│   ├── source_fingerprint.py# Code hash that invalidates the disk caches
│   ├── bdo_thumbnail_cache.py# Icon thumbnail cache (SQLite, next to the PAZ files)
│   ├── bdo_records_cache.py# Parsed table cache (SQLite, next to the PAZ files)
│   ├── bdo_paz_extract.py  # File extraction logic
│   └── bdo_paz_reader.py   # PAZ archive parser
│
├── tests/                  # Unit test framework and gitignored fixtures
│   ├── framework.py        # Public re-export for test helpers
│   ├── specs.py            # DeclaredCountTest, TargetTest, SchemaTest, RangeTest
│   ├── declared.py         # Row counts read from the input for DeclaredCountTest
│   ├── case_input.py       # CaseInput: the bytes a case parsed
│   ├── models.py           # HandlerCase, HandlerResult
│   ├── runner.py           # run_case()
│   ├── fixtures.py         # Auto-fetches test inputs from PAZ folder
│   ├── fixture_sync.py     # Refreshes fixtures when the client changes
│   └── fixtures/           # Gitignored cached binaries
│
├── ui/                     # Web UI (HTML + JS + CSS)
│   ├── index.html
│   ├── app.js              # Entry point, assembles feature modules
│   ├── style.css           # CSS entry point, imports css/ modules
│   ├── css/                # Per-component stylesheets (numbered load order)
│   └── js/
│       ├── core/           # Shared state and helpers
│       └── features/       # Feature modules (tree, search, extraction, …)
│
└── handlers/               # Format preview plugins (auto-loaded)
    ├── dbss_handler.py     # DBSS entry point
    ├── _dbss/              # DBSS format implementations
    │   ├── common/         # Shared binary/HTML helpers
    │   ├── title/
    │   ├── titleoffset/
    │   ├── titlebuff/
    │   ├── mentalcard/
    │   ├── mentaltheme/
    │   ├── knowledgelearning/
    │   ├── npcgift/
    │   ├── quest/
    │   └── questgroup/
    └── _common/            # Helpers shared across formats
        └── loc.py

docs/
├── handler.md              # Guide for writing preview handlers
├── style-guide.md          # UI color palette and component reference
└── file-formats/           # Per-format binary layout documentation
```

---

## Disclaimer

This project is for research purposes only. BDO game data is copyright Pearl Abyss. Do not redistribute extracted game assets.
