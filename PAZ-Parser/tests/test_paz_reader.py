from __future__ import annotations

import logging
import struct
from pathlib import Path

import pytest

from paz.bdo_ice import BDO_ICE_KEY, IceCipher
from paz.bdo_paz_reader import parse_paz_file, parse_paz_files

# Path block strings: 0 and 1 are folders, 2 and 3 file names. Padded with
# nulls to the 8-byte ICE block, as the archive stores it.
_STRINGS = [b"ui/", b"gamecommondata/", b"icon.dds", b"quest.dbss"]


def _archive(tmp_path: Path, rows: list[tuple[int, int, int, int, int]], name: str = "PAD00001.PAZ") -> Path:
    plain = b"".join(s + b"\x00" for s in _STRINGS)
    plain += b"\x00" * (-len(plain) % 8)
    path_block = IceCipher(BDO_ICE_KEY).encrypt(plain)
    infos = b"".join(struct.pack("<IIIIII", 0, *row) for row in rows)
    archive = tmp_path / name
    archive.write_bytes(struct.pack("<III", 0, len(rows), len(path_block)) + infos + path_block)
    return archive


def test_parse_paz_file_joins_folder_and_file_names(tmp_path: Path) -> None:
    archive = _archive(tmp_path, [(0, 2, 100, 40, 80), (1, 3, 140, 16, 16)])

    entries = parse_paz_file(archive)

    assert [(e.internal_path, e.offset, e.compressed_size, e.uncompressed_size) for e in entries] == [
        ("ui/icon.dds", 100, 40, 80),
        ("gamecommondata/quest.dbss", 140, 16, 16),
    ]
    assert {e.archive_name for e in entries} == {"PAD00001.PAZ"}


def test_parse_paz_file_names_an_out_of_range_string_unknown(tmp_path: Path) -> None:
    archive = _archive(tmp_path, [(0, 999, 100, 40, 80)])

    (entry,) = parse_paz_file(archive)

    assert entry.internal_path == "unknown/PAD00001_0_c40_u80.bin"


def test_parse_paz_files_keeps_archive_order_and_skips_a_missing_one(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    first = _archive(tmp_path, [(0, 2, 100, 40, 80)], name="PAD00001.PAZ")
    second = _archive(tmp_path, [(1, 3, 140, 16, 16)], name="PAD00003.PAZ")
    missing = tmp_path / "PAD00002.PAZ"

    with caplog.at_level(logging.WARNING):
        entries = parse_paz_files([first, missing, second])

    assert [(e.archive_name, e.internal_path) for e in entries] == [
        ("PAD00001.PAZ", "ui/icon.dds"),
        ("PAD00003.PAZ", "gamecommondata/quest.dbss"),
    ]
    assert "PAD00002.PAZ" in caplog.text
