"""`browser.py --index [<kind>] [--id N]`: what a lookup index holds.

Indexes come from `paz_browser_indexes.cache`, built first when missing or
stale, exactly as the app loads them. Without a kind, lists every kind and its
entry count.
"""
from __future__ import annotations

import argparse

from _common.lookup_index import IndexKind, index_entries, index_size, is_index_loaded, lookup

from .errors import CliError
from .record_output import write_records
from .records import output_format
from .session import open_session
from .stdio import error, progress
from .values import parse_int


def parse_kind(text: str) -> IndexKind:
    """An `IndexKind` by value (`character_item`) or name (`CHARACTER_ITEM`)."""
    wanted = text.strip().lower()
    for kind in IndexKind:
        if wanted in (kind.value, kind.name.lower()):
            return kind
    kinds = ", ".join(kind.value for kind in IndexKind)
    raise CliError(f"unknown index kind '{text}'. Kinds: {kinds}")


def parse_id(text: str | None) -> int | None:
    if text is None:
        return None
    try:
        return parse_int(text)
    except ValueError:
        raise CliError(f"--id needs an integer (decimal or 0x hex), got '{text}'.") from None


def kind_records() -> list[dict]:
    return [
        {"kind": kind.value, "loaded": is_index_loaded(kind), "entries": index_size(kind)}
        for kind in IndexKind
    ]


def entry_records(kind: IndexKind, entity_id: int | None, limit: int | None) -> list[dict]:
    """One entry, or every entry sorted by ID. Raises when the ID is absent."""
    if entity_id is not None:
        value = lookup(kind, entity_id)
        if value is None:
            raise CliError(f"ID {entity_id} is not in the {kind.value} index.")
        return [{"id": entity_id, "value": value}]

    entries = sorted(index_entries(kind).items())
    if limit is not None:
        entries = entries[:limit]
    return [{"id": key, "value": value} for key, value in entries]


def run_index(args: argparse.Namespace) -> int:
    try:
        kind = parse_kind(args.index) if args.index else None
        entity_id = parse_id(args.id)
        output = output_format(args)

        open_session(args.paz_folder, load_loc=False)
        if kind is None:
            write_records(kind_records(), output)
            return 0

        if not is_index_loaded(kind):
            raise CliError(f"the {kind.value} index is not loaded (its source tables are missing).")
        records = entry_records(kind, entity_id, args.limit)
    except CliError as ex:
        error(str(ex))
        return 1

    write_records(records, output)
    if entity_id is None:
        progress(f"{len(records):,} of {index_size(kind):,} entries in {kind.value}.")
    return 0
