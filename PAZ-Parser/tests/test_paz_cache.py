"""The PAZ index cache: columns on disk, entries back, anything else a miss."""
from __future__ import annotations

import pickle
from pathlib import Path

from bdo_models import PazEntry
from paz.bdo_cache import CACHE_FILE, CACHE_FORMAT, load_cache, save_cache

_ENTRIES = [
    PazEntry("PAD00001.PAZ", "gamecommondata/binary/quest.dbss", 12, 400, 900, 0, 0),
    PazEntry("PAD00002.PAZ", "ui_texture/icon/Old/Pet.dds", 0, 4_294_967_295, 16, 0, 0),
    PazEntry("PAD00001.PAZ", "readme.txt", 412, 8, 8, 0, 0),
]


def _saved_columns(tmp_path: Path) -> dict:
    save_cache(tmp_path, 3458, _ENTRIES)
    with (tmp_path / CACHE_FILE).open("rb") as f:
        return pickle.load(f)


def _write(tmp_path: Path, data: object) -> None:
    (tmp_path / CACHE_FILE).write_bytes(pickle.dumps(data))


def test_saved_entries_load_back_in_order(tmp_path: Path) -> None:
    save_cache(tmp_path, 3458, _ENTRIES)

    loaded = load_cache(tmp_path)

    assert loaded == (3458, _ENTRIES)
    assert loaded is not None and all(type(entry) is PazEntry for entry in loaded[1])


def test_an_empty_client_round_trips(tmp_path: Path) -> None:
    save_cache(tmp_path, 1, [])

    assert load_cache(tmp_path) == (1, [])


def test_a_missing_cache_is_a_miss(tmp_path: Path) -> None:
    assert load_cache(tmp_path) is None


def test_the_old_pickled_list_format_is_a_miss(tmp_path: Path) -> None:
    _write(tmp_path, {"version": 3458, "entries": list(_ENTRIES)})

    assert load_cache(tmp_path) is None


def test_another_format_number_is_a_miss(tmp_path: Path) -> None:
    columns = _saved_columns(tmp_path)
    _write(tmp_path, {**columns, "format": CACHE_FORMAT + 1})

    assert load_cache(tmp_path) is None


def test_columns_of_different_lengths_are_a_miss(tmp_path: Path) -> None:
    columns = _saved_columns(tmp_path)
    _write(tmp_path, {**columns, "paths": columns["paths"][:-1]})

    assert load_cache(tmp_path) is None


def test_an_archive_index_out_of_range_is_a_miss(tmp_path: Path) -> None:
    columns = _saved_columns(tmp_path)
    _write(tmp_path, {**columns, "archives": columns["archives"][:1]})

    assert load_cache(tmp_path) is None


def test_a_file_that_is_not_a_pickle_is_a_miss(tmp_path: Path) -> None:
    (tmp_path / CACHE_FILE).write_bytes(b"not a cache")

    assert load_cache(tmp_path) is None
