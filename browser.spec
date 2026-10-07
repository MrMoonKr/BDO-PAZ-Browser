# PyInstaller spec for the Windows build. From the repo root:
#
#     python -m pip install -r PAZ-Parser/requirements-build.txt
#     python build.py
#
# build.py runs PyInstaller with this spec, checks the result and zips it.
# Output: dist/BDO-PAZ-Browser/ with BDO-PAZ-Browser.exe (windowed) and
# bdo-paz-cli.exe (console, since a windowed exe has no stdout), sharing one
# _internal folder. BDO_APP_VERSION and BDO_APP_COMMIT set the version and
# commit (build.py passes them); without them, today's date and git's HEAD.
#
# The handlers go in as loose files under _internal/handlers (the bundled
# handler pack), not into the archive, so their source is hashed for the
# caches and a pack can replace them. The archive holds the core plus the
# standard library modules handler code may import (handler_api.py).

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(SPECPATH)
SRC = ROOT / "PAZ-Parser"
sys.path.insert(0, str(SRC))

from app_version import BUILD_INFO_NAME, parse_version  # noqa: E402
from handler_api import STDLIB_MODULES  # noqa: E402

APP_NAME = "BDO-PAZ-Browser"
CLI_NAME = "bdo-paz-cli"
ICON = str(SRC / "ui" / "favicon.ico")
# Top-level names under handlers/: they must come from the loose files, never the archive.
HANDLER_MODULES = sorted(
    path.stem if path.is_file() else path.name
    for path in (SRC / "handlers").iterdir()
    if path.suffix == ".py" or (path.is_dir() and path.name != "__pycache__")
)


def _git_commit() -> str:
    """The short commit hash, or "unknown" outside a git checkout."""
    try:
        result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    except OSError:
        return "unknown"
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def _build_info_file() -> str:
    version = os.environ.get("BDO_APP_VERSION") or time.strftime("%Y.%m.%d")
    parse_version(version)  # fail the build on a malformed version
    commit = os.environ.get("BDO_APP_COMMIT") or _git_commit()
    path = Path(workpath) / BUILD_INFO_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"version": version, "commit": commit}), encoding="utf-8")
    return str(path)


a = Analysis(
    [str(ROOT / "browser.py")],
    pathex=[str(SRC)],
    datas=[(_build_info_file(), ".")],
    hiddenimports=sorted(STDLIB_MODULES),
    excludes=[*HANDLER_MODULES, "tests", "conftest", "bench", "pytest", "_pytest", "pyright"],
    noarchive=False,
)
pyz = PYZ(a.pure)

gui = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    console=False,
    icon=ICON,
)
cli = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=CLI_NAME,
    console=True,
    icon=ICON,
)


def _handler_pack() -> list[tuple[str, str, str]]:
    """handlers/ without tests or bytecode. Tree() can't do it: an exclude
    pattern is a glob only when it starts with `*`, so `test_*.py` matches nothing."""
    handlers_dir = SRC / "handlers"
    return [
        (str(Path("handlers") / path.relative_to(handlers_dir)), str(path), "DATA")
        for path in sorted(handlers_dir.rglob("*"))
        if path.is_file()
        and "__pycache__" not in path.parts
        and not path.name.startswith("test_")
        and path.suffix != ".pyc"
    ]


ui = Tree(str(SRC / "ui"), prefix="ui")

coll = COLLECT(
    gui,
    cli,
    a.binaries,
    a.datas,
    ui,
    _handler_pack(),
    name=APP_NAME,
)
