"""What a benchmark decodes, and the stages it times on it.

A workload is one PAZ entry (`--entry`) or one whole archive (`--archive`).

On an entry, `decrypt` and `decompress` work on bytes already in memory, so
disk speed and the OS file cache stay out of their numbers. `read` is the
whole path the app takes to open a file, disk read included. `extract` is what
`extract_all` does per file: `read`, then the size check and the write to disk.

On an archive, `extract` runs `extract_all`'s loop over every entry in it. It
leaves out `extract_all`'s meta file parse, which reads every entry of the
client on each call (over a minute) and would swamp the decode time.
"""
from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from bdo_models import PazEntry
from cli.errors import CliError
from cli.parsed_file import find_entry
from cli.session import open_session
from paz.bdo_paz_extract import extract_entries, extract_entry
from paz.bdo_payload_reader import (
    bdo_decompress,
    ice_decrypt_bytes,
    is_encrypted,
    needs_decompress,
    read_entry_payload,
    read_raw_payload,
)

from .results import FixtureInfo

# A 14 MB texture (4.4 MB stored) that is both encrypted and compressed, so
# every entry stage has work to do.
DEFAULT_ENTRY = "morningland_boss_03_02_full.dds"
# A median-size archive (9 MB, about 800 files) mixing .bwp, .xml, .bss,
# .dbss and more, compressed and stored, encrypted and plain.
DEFAULT_ARCHIVE = "pad05889.paz"
STAGE_NAMES = ("decrypt", "decompress", "read", "extract")
_HASH_CHUNK_BYTES = 1024 * 1024


@dataclass(frozen=True)
class Stage:
    name: str
    run: Callable[[], object]


@dataclass(frozen=True)
class Workload:
    info: FixtureInfo
    # Builds the stages; `extract` writes into the scratch folder it is given.
    build_stages: Callable[[Path], list[Stage]]


def load_entry_workload(paz_folder: str | None, name: str) -> Workload:
    """Find `name` in the PAZ folder and read its stored bytes into memory."""
    paz_root, entries = _open_folder(paz_folder)
    entry = find_entry(entries, name)
    archive_path = paz_root / entry.archive_name
    try:
        raw = read_raw_payload(archive_path, entry)
    except (OSError, ValueError) as ex:
        raise CliError(f"cannot read {entry.internal_path}: {ex}") from ex
    decrypted = ice_decrypt_bytes(raw) if is_encrypted(entry) else raw

    info = FixtureInfo(
        name=entry.internal_path,
        files=1,
        stored_bytes=entry.compressed_size,
        size_bytes=entry.uncompressed_size,
        sha256=hashlib.sha256(raw).hexdigest(),
    )
    return Workload(info, lambda scratch: _entry_stages(archive_path, entry, raw, decrypted, scratch))


def load_archive_workload(paz_folder: str | None, archive: str) -> Workload:
    """Every entry stored in `archive` (`pad05889.paz`, any case, extension optional)."""
    paz_root, entries = _open_folder(paz_folder)
    wanted = archive_file_name(archive)
    in_archive = [entry for entry in entries if entry.archive_name.lower() == wanted]
    if not in_archive:
        raise CliError(f"no file of the client is stored in {wanted}.")
    archive_path = paz_root / in_archive[0].archive_name

    info = FixtureInfo(
        name=wanted,
        files=len(in_archive),
        stored_bytes=sum(entry.compressed_size for entry in in_archive),
        size_bytes=sum(entry.uncompressed_size for entry in in_archive),
        sha256=_file_sha256(archive_path),
    )
    return Workload(
        info,
        lambda scratch: [Stage("extract", lambda: _extract_archive(paz_root, scratch, in_archive))],
    )


def archive_file_name(text: str) -> str:
    name = text.strip().lower()
    return name if name.endswith(".paz") else f"{name}.paz"


def parse_stage_names(text: str | None) -> list[str] | None:
    """`--stages decrypt,read` as a list; None (every stage) when not given."""
    if text is None:
        return None
    names = [name.strip().lower() for name in text.split(",") if name.strip()]
    unknown = [name for name in names if name not in STAGE_NAMES]
    if unknown or not names:
        raise CliError(f"--stages takes a comma list of {', '.join(STAGE_NAMES)}, got '{text}'.")
    return names


def select_stages(stages: Sequence[Stage], wanted: Sequence[str] | None, workload_name: str) -> list[Stage]:
    """The `wanted` stages in pipeline order, or every stage when None."""
    if wanted is None:
        return list(stages)
    available = [stage.name for stage in stages]
    missing = [name for name in wanted if name not in available]
    if missing:
        raise CliError(
            f"{workload_name} has no {', '.join(missing)} stage; it has {', '.join(available)}."
        )
    return [stage for stage in stages if stage.name in wanted]


def _open_folder(paz_folder: str | None) -> tuple[Path, list[PazEntry]]:
    api = open_session(paz_folder, load_loc=False, load_indexes=False)
    if api.paz_root is None:
        raise CliError("the PAZ folder did not load.")
    return api.paz_root, api.entries


def _entry_stages(
    archive_path: Path,
    entry: PazEntry,
    raw: bytes,
    decrypted: bytes,
    scratch: Path,
) -> list[Stage]:
    """The stages that apply to the entry, in pipeline order."""
    stages: list[Stage] = []
    if is_encrypted(entry):
        stages.append(Stage("decrypt", lambda: ice_decrypt_bytes(raw)))
    if needs_decompress(entry, decrypted):
        stages.append(Stage("decompress", lambda: bdo_decompress(decrypted, expected_size=entry.uncompressed_size)))
    stages.append(Stage("read", lambda: read_entry_payload(archive_path, entry)))
    stages.append(
        Stage(
            "extract",
            lambda: extract_entry(
                paz_root=archive_path.parent,
                output_root=scratch,
                entry=entry,
                overwrite=True,
                flat=True,
            ),
        )
    )
    return stages


def _extract_archive(paz_root: Path, scratch: Path, entries: list[PazEntry]) -> None:
    counts = extract_entries(paz_root, scratch, entries, overwrite=True)
    if counts.failed:
        raise CliError(f"{counts.failed} of {len(entries)} files failed to extract; the log above names them.")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(_HASH_CHUNK_BYTES):
                digest.update(chunk)
    except OSError as ex:
        raise CliError(f"cannot read {path}: {ex}") from ex
    return digest.hexdigest()
