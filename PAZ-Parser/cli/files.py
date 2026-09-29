"""`browser.py --list <pattern>` and `--file <pattern>`: find and extract files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from api.bdo_api_helpers import _norm, path_matcher
from bdo_models import PazEntry
from paz.bdo_paz_extract import extract_entry

from .errors import CliError
from .session import open_session
from .stdio import error, progress


def match_entries(entries: list[PazEntry], pattern: str) -> list[PazEntry]:
    """Entries matching `pattern` by the GUI search rules, in meta file order."""
    is_hit = path_matcher(pattern)
    return [entry for entry in entries if is_hit(_norm(entry.internal_path))]


def _open_matches(args: argparse.Namespace, pattern: str) -> tuple[Path, list[PazEntry]]:
    api = open_session(args.paz_folder, load_loc=False, load_indexes=False)
    matches = match_entries(api.entries, pattern)
    if not matches:
        raise CliError(f"no files found matching '{pattern}'.")
    assert api.paz_root is not None  # set by open_session
    return api.paz_root, matches


def run_list(args: argparse.Namespace) -> int:
    try:
        _, matches = _open_matches(args, args.list)
    except CliError as ex:
        error(str(ex))
        return 1

    progress(f"{len(matches):,} file(s) matching '{args.list}':")
    for entry in matches:
        size_kb = entry.uncompressed_size / 1024
        print(f"  {entry.internal_path}  ({size_kb:,.1f} KB)")
    return 0


def run_extract(args: argparse.Namespace) -> int:
    try:
        paz_root, matches = _open_matches(args, args.file)
    except CliError as ex:
        error(str(ex))
        return 1

    output_root = Path(args.output) if args.output else Path.cwd()
    print(f"Found {len(matches):,} file(s). Extracting to {output_root} …\n")

    extracted = skipped = failed = 0
    for i, entry in enumerate(matches, 1):
        label = f"[{i}/{len(matches)}]"
        try:
            result = extract_entry(paz_root=paz_root, output_root=output_root, entry=entry, overwrite=False, flat=True)
            if result == "skipped":
                skipped += 1
                print(f"  {label} SKIP  {entry.internal_path}")
            else:
                extracted += 1
                print(f"  {label} OK    {entry.internal_path}")
        except Exception as ex:
            failed += 1
            print(f"  {label} FAIL  {entry.internal_path}: {ex}", file=sys.stderr)

    print(f"\nDone, {extracted} extracted, {skipped} skipped, {failed} failed.")
    return 1 if failed else 0
