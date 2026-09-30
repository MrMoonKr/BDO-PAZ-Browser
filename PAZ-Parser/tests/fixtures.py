from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from .models import HandlerCase


PAZ_PARSER_DIR = Path(__file__).parents[1].resolve()
REPO_ROOT = PAZ_PARSER_DIR.parent
FIXTURES_DIR = Path(
    os.environ.get("PAZ_PARSER_FIXTURES_DIR", PAZ_PARSER_DIR / "tests" / "fixtures")
).resolve()


class FixtureFetchError(Exception):
    """A fixture could not be extracted from the client or copied from the game folder."""


def ensure_fixtures(case: HandlerCase) -> dict[str, Path]:
    fixture_paths = resolve_fixture_paths(case)
    missing = [name for name, path in fixture_paths.items() if not path.exists()]
    if missing:
        try:
            fetch_fixtures(missing)
        except FixtureFetchError as ex:
            pytest.fail(str(ex))

    missing = [name for name, path in fixture_paths.items() if not path.exists()]
    if missing:
        pytest.fail(f"fixtures unavailable after fetch: {', '.join(missing)}")

    return fixture_paths


def load_binary_fixture(name: str) -> bytes:
    """A `gamecommondata/binary` fixture, for a parser test without a handler."""
    case = HandlerCase(
        handler_name=name,
        data_file=name,
        companion_files={},
        loc_file=None,
        uses_loc=False,
        loc_fields=[],
        internal_path=f"gamecommondata/binary/{name}",
        tests=[],
    )
    return ensure_fixtures(case)[name].read_bytes()


def resolve_fixture_paths(case: HandlerCase) -> dict[str, Path]:
    paths: dict[str, Path] = {str(case.data_file): FIXTURES_DIR / case.data_file}
    for relative_path in case.companion_files.values():
        paths[str(relative_path)] = FIXTURES_DIR / relative_path
    if case.loc_file is not None:
        paths[str(case.loc_file)] = FIXTURES_DIR / case.loc_file
    return paths


def fetch_fixtures(fixture_names: list[str]) -> None:
    """Fetch into a staging folder, then replace, so a failed fetch keeps the old copy.

    `browser.py --file` never overwrites an existing file, so a refresh cannot
    extract straight into the fixtures folder.
    """
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=FIXTURES_DIR, prefix=".fetch-") as staging:
        staging_dir = Path(staging)
        for fixture_name in fixture_names:
            _fetch_fixture(fixture_name, staging_dir)
            os.replace(staging_dir / fixture_name, FIXTURES_DIR / fixture_name)


def _fetch_fixture(fixture_name: str, output_dir: Path) -> None:
    command = [
        sys.executable,
        str(REPO_ROOT / "browser.py"),
        "--file",
        fixture_name,
        "--output",
        str(output_dir),
    ]
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        # The CLI writes UTF-8 whatever the console code page.
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.returncode == 0 and (output_dir / fixture_name).exists():
        return
    if copy_external_fixture(fixture_name, output_dir):
        return

    details = "\n".join(part for part in (result.stdout, result.stderr) if part)
    raise FixtureFetchError(
        f"could not fetch fixture {fixture_name!r} via browser.py --file. "
        f"Check PAZ folder config or pass --paz-folder manually once.\n{details}"
    )


def copy_external_fixture(fixture_name: str, output_dir: Path) -> bool:
    source = find_external_fixture(fixture_name)
    if source is None:
        return False

    shutil.copy2(source, output_dir / fixture_name)
    return True


def configured_paz_folder() -> Path | None:
    """The PAZ folder last opened in the GUI, from `paz_config.json`."""
    config_path = PAZ_PARSER_DIR / "paz_config.json"
    try:
        last_folder = json.loads(config_path.read_text()).get("last_folder", "")
    except (OSError, ValueError):
        return None

    return Path(last_folder) if last_folder else None


def find_external_fixture(fixture_name: str) -> Path | None:
    paz_folder = configured_paz_folder()
    if paz_folder is None:
        return None

    game_root = paz_folder.parent
    candidates = [
        game_root / fixture_name,
        game_root / "ads" / fixture_name,
        paz_folder / fixture_name,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None
