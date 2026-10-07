from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from bdo_models import PazEntry
from bdo_preview import PreviewHandler, get_handler

from _common.lookup_index import IndexKind, init_index

from .case_input import CaseInput
from .fixtures import ensure_fixtures
from .loc_counter import LOC_STATE_NAMES, null_loc_counter, patch_loc_counter, reset_loc
from .models import HandlerCase, HandlerResult, IndexSource


@dataclass(frozen=True)
class LoadedCase:
    """A case's handler with its fixture bytes, ready to call."""

    handler: PreviewHandler
    entry: PazEntry
    data: bytes
    companions: dict[str, bytes]


# Parsed LOC state per fixture path. Parsing takes seconds, and cases with
# and without LOC interleave, so a case restores the parsed state instead.
_parsed_loc: dict[Path, tuple[object, ...]] = {}


def _load_loc(path: Path | None) -> None:
    """Load the LOC fixture at `path`, or clear LOC when `path` is None."""
    import _common.loc as loc

    reset_loc()
    if path is None:
        return

    state = _parsed_loc.get(path)
    if state is None:
        loc.init_loc(path.read_bytes())
        _parsed_loc[path] = tuple(getattr(loc, name) for name in LOC_STATE_NAMES)
        return

    for name, value in zip(LOC_STATE_NAMES, state):
        setattr(loc, name, value)


def load_case(case: HandlerCase) -> LoadedCase:
    """Fetch the case's fixtures, load its LOC (or clear it) and resolve its handler."""
    fixture_paths = ensure_fixtures(case)
    _load_loc(None if case.loc_file is None else fixture_paths[str(case.loc_file)])

    data = fixture_paths[str(case.data_file)].read_bytes()
    companions = {
        basename: fixture_paths[str(relative_path)].read_bytes()
        for basename, relative_path in case.companion_files.items()
    }

    entry = PazEntry(
        archive_name="",
        internal_path=case.internal_path,
        offset=0,
        compressed_size=0,
        uncompressed_size=0,
        compression_type=0,
        encryption_type=0,
    )
    suffix = Path(case.internal_path).suffix
    handler = get_handler(Path(case.internal_path).name, suffix)
    return LoadedCase(handler, entry, data, companions)


@contextmanager
def _installed_indexes(indexes: Mapping[IndexKind, IndexSource]) -> Iterator[None]:
    """Install the case's lookup indexes for the duration of the block."""
    for kind, source in indexes.items():
        init_index(kind, source() if callable(source) else source)
    try:
        yield
    finally:
        for kind in indexes:
            init_index(kind, None)


def run_case(case: HandlerCase) -> HandlerResult:
    loaded = load_case(case)

    loc_counter = patch_loc_counter() if case.uses_loc else null_loc_counter()
    with loc_counter as loc_stats, _installed_indexes(case.lookup_indexes):
        start = perf_counter()
        records = loaded.handler.get_records(loaded.data, loaded.entry, loaded.companions)
        elapsed_ms = (perf_counter() - start) * 1000

    if case.record_mapper is not None:
        records = [case.record_mapper(record) for record in records]

    result = HandlerResult(
        row_count=len(records),
        elapsed_ms=elapsed_ms,
        loc_total_calls=loc_stats.total,
        loc_fallback_count=loc_stats.misses,
        source=CaseInput(loaded.data, loaded.companions),
        records=records,
    )
    for spec in case.tests:
        try:
            result.passed.append(result.check(spec))
        except AssertionError as exc:
            result.failed.append(str(exc))

    return result
