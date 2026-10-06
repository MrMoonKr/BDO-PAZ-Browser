from __future__ import annotations

import logging
import struct
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .bdo_payload_reader import ice_decrypt_many
from bdo_models import PazEntry

# Archive header: crc, file count, path block length.
_HEADER = struct.Struct("<III")
# One file table row: crc, folder string, file string, offset, sizes.
_FILE_INFO = struct.Struct("<IIIIII")
# Path blocks average about 2 KB, so a batch decrypts about 1 MB at once:
# large enough that numpy's per-call cost is gone, small enough that the
# batch adds little to peak memory.
_ARCHIVES_PER_BATCH = 500


@dataclass(frozen=True)
class _ArchiveTables:
    """An archive's file table and its still encrypted path block."""

    path: Path
    file_infos: bytes
    path_block: bytes


def parse_paz_file(paz_path: Path) -> list[PazEntry]:
    """Every entry stored in one archive."""
    return parse_paz_files([paz_path])


def parse_paz_files(paz_paths: Sequence[Path]) -> list[PazEntry]:
    """Every entry stored in the archives, in order.

    The archives are read in batches, and a batch's path blocks are decrypted
    in one call: thousands of small calls cost more in numpy overhead than in
    decrypting. A missing archive is logged and skipped.
    """
    log_entries = logging.getLogger().isEnabledFor(logging.DEBUG)
    entries: list[PazEntry] = []
    for start in range(0, len(paz_paths), _ARCHIVES_PER_BATCH):
        tables = _read_tables(paz_paths[start : start + _ARCHIVES_PER_BATCH])
        path_blocks = ice_decrypt_many([table.path_block for table in tables])
        for table, path_block in zip(tables, path_blocks):
            entries.extend(_build_entries(table, path_block, log_entries))
    return entries


def _read_tables(paz_paths: Sequence[Path]) -> list[_ArchiveTables]:
    tables: list[_ArchiveTables] = []
    for paz_path in paz_paths:
        try:
            tables.append(_read_archive_tables(paz_path))
        except FileNotFoundError:
            logging.warning("Referenced archive not found: %s", paz_path)
    return tables


def _read_archive_tables(paz_path: Path) -> _ArchiveTables:
    with paz_path.open("rb") as file:
        header_data: bytes = file.read(_HEADER.size)
        if len(header_data) != _HEADER.size:
            raise ValueError(f"Invalid PAZ header: {paz_path}")

        crc, file_count, path_length = _HEADER.unpack(header_data)

        logging.debug(
            "PAZ header | file=%s crc=%08x file_count=%d path_length=%d",
            paz_path.name,
            crc,
            file_count,
            path_length,
        )

        raw_infos_size: int = file_count * _FILE_INFO.size
        raw_infos: bytes = file.read(raw_infos_size)
        if len(raw_infos) != raw_infos_size:
            raise ValueError(f"Invalid file table in: {paz_path}")

        path_block_encrypted: bytes = file.read(path_length)
        if len(path_block_encrypted) != path_length:
            raise ValueError(f"Invalid path block in: {paz_path}")

    return _ArchiveTables(paz_path, raw_infos, path_block_encrypted)


def _build_entries(table: _ArchiveTables, path_block: bytes, log_entries: bool) -> list[PazEntry]:
    """The archive's entries, named from its decrypted path block.

    `log_entries` is checked once per archive: a disabled `logging.debug`
    per entry cost more than reading the entry.
    """
    archive_name = table.path.name
    strings = _parse_string_table(path_block, len(path_block))
    entries: list[PazEntry] = []

    for index, (
        _file_crc,
        folder_id,
        file_id,
        offset,
        compressed_size,
        original_size,
    ) in enumerate(_FILE_INFO.iter_unpack(table.file_infos)):

        # Reconstruct path: strings[folder_id] acts as the directory,
        # strings[file_id] acts as the filename.
        try:
            internal_path: str = strings[folder_id] + strings[file_id]
        except IndexError:
            logging.warning(
                "PAZ path out of range | file=%s index=%d folder_id=%d file_id=%d strings=%d",
                archive_name,
                index,
                folder_id,
                file_id,
                len(strings),
            )
            internal_path = (
                f"unknown/{table.path.stem}_{index}"
                f"_c{compressed_size}_u{original_size}.bin"
            )

        entries.append(
            PazEntry(
                archive_name=archive_name,
                internal_path=internal_path,
                offset=offset,
                compressed_size=compressed_size,
                uncompressed_size=original_size,
                compression_type=0,
                encryption_type=0,
            )
        )

        if log_entries:
            logging.debug(
                "PAZ entry | file=%s index=%d path=%s offset=%d compressed=%d original=%d",
                archive_name,
                index,
                internal_path,
                offset,
                compressed_size,
                original_size,
            )

    return entries


def _parse_string_table(data: bytes, length: int) -> list[str]:
    """
    Parse the null-terminated string table from a decrypted path block.

    Each entry is a C string (null-terminated). The table is `length` bytes.
    """
    strings: list[str] = []
    offset = 0
    while offset < length:
        try:
            end = data.index(b"\x00", offset)
        except ValueError:
            # No null terminator, take remainder as last string.
            strings.append(data[offset:length].decode("utf-8", errors="replace"))
            break
        strings.append(data[offset:end].decode("utf-8", errors="replace"))
        offset = end + 1
    return strings
