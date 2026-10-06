from dataclasses import dataclass
from typing import NamedTuple


class PazEntry(NamedTuple):
    """One file stored in a PAZ archive.

    A NamedTuple, not a dataclass: a client holds about 870,000 of them, and
    a tuple has no per-instance `__dict__` (about 85 MB less) and can be
    built in C when the index cache loads (`paz/bdo_cache.py`).
    """

    archive_name: str
    internal_path: str
    offset: int
    compressed_size: int
    uncompressed_size: int
    compression_type: int
    encryption_type: int


@dataclass(frozen=True)
class PazTable:
    paz_file_id: int
    crc: int
    size: int


@dataclass(frozen=True)
class MetaFile:
    version: int
    paz_file_count: int
    paz_files: list[PazTable]
