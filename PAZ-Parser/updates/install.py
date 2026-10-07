"""Install a release: download and check the zip, unpack it next to the app, swap.

A running exe can't replace its own folder, so the swap is a plain `.cmd`
helper written next to the app folder (not into a temp folder, which
antivirus tools trust less). It waits for the app to exit, renames the app
folder to `<name>.old` and the unpacked one into place (same drive, so a
rename), and moves `data\\` (the default Data Folder) across. It then runs
the new `bdo-paz-cli.exe --handlers`: when that fails, it puts the old
folder back. `<name>.old` is deleted only after that check passed.

Files the app downloads itself carry no browser download mark, so the new
exe starts without a SmartScreen warning.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app_dirs import PORTABLE_FOLDER

from .releases import Release, UpdateError

APP_EXE = "BDO-PAZ-Browser.exe"
CLI_EXE = "bdo-paz-cli.exe"
# The folder inside the release zip.
ZIP_FOLDER = "BDO-PAZ-Browser"
DOWNLOAD_TIMEOUT = 30
_CHUNK = 256 * 1024
_SHA256_RE = re.compile(r"^([0-9a-fA-F]{64})\b")
_VERSION_IN_NAME_RE = re.compile(r"-v(\d{4}\.\d{1,2}\.\d{1,2}(?:\.\d+)?)-windows\.zip$")

Progress = Callable[[int, int], None]


@dataclass(frozen=True)
class PreparedUpdate:
    """A checked release unpacked next to the running app, ready to swap in."""

    version: str
    app_dir: Path
    new_dir: Path


def running_app_dir() -> Path:
    """The folder of the running exe."""
    return Path(sys.executable).resolve().parent


def download(url: str, target: Path, progress: Progress | None = None) -> None:
    """Download `url` to `target` through a `.part` file. Raises UpdateError."""
    partial = target.with_name(f"{target.name}.part")
    request = urllib.request.Request(url, headers={"User-Agent": "BDO-PAZ-Browser"})
    try:
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response, partial.open("wb") as file:
            total = int(response.headers.get("Content-Length") or 0)
            done = 0
            while chunk := response.read(_CHUNK):
                file.write(chunk)
                done += len(chunk)
                if progress is not None:
                    progress(done, total)
        os.replace(partial, target)
    except OSError as ex:
        partial.unlink(missing_ok=True)
        raise UpdateError(f"could not download {url}: {ex}") from ex


def read_sha256_file(path: Path) -> str:
    """The hash in a `<hash>  <name>` file, as `build.py` writes it."""
    try:
        match = _SHA256_RE.match(path.read_text(encoding="utf-8").strip())
    except OSError as ex:
        raise UpdateError(f"could not read {path.name}: {ex}") from ex
    if match is None:
        raise UpdateError(f"{path.name} holds no SHA-256 hash")
    return match.group(1).lower()


def check_sha256(path: Path, expected: str) -> None:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(_CHUNK):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise UpdateError(f"{path.name} does not match its SHA-256; the download is broken, try again")


def version_of_zip(path: Path) -> str:
    """The version in a release zip's name, `BDO-PAZ-Browser-v<version>-windows.zip`."""
    match = _VERSION_IN_NAME_RE.search(path.name)
    if match is None:
        raise UpdateError(f"{path.name} is not named like a release zip (BDO-PAZ-Browser-v<version>-windows.zip)")
    return match.group(1)


def fetch_release(release: Release, app_dir: Path, progress: Progress | None = None) -> Path:
    """Download the release zip and its hash next to `app_dir`, checked. Returns the zip."""
    zip_path = app_dir.parent / f"{app_dir.name}.update-v{release.version}.zip"
    sha_path = zip_path.with_name(f"{zip_path.name}.sha256")
    download(release.sha256_url, sha_path)
    download(release.zip_url, zip_path, progress)
    try:
        check_sha256(zip_path, read_sha256_file(sha_path))
    except UpdateError:
        zip_path.unlink(missing_ok=True)
        raise
    finally:
        sha_path.unlink(missing_ok=True)
    return zip_path


def unpack(zip_path: Path, version: str, app_dir: Path) -> PreparedUpdate:
    """Unpack a checked release zip to `<app>.new` next to `app_dir`."""
    new_dir = app_dir.parent / f"{app_dir.name}.new"
    unpacking = app_dir.parent / f"{app_dir.name}.unpacking"
    for leftover in (new_dir, unpacking):
        shutil.rmtree(leftover, ignore_errors=True)
    try:
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(unpacking)
        inner = unpacking / ZIP_FOLDER
        if not (inner / APP_EXE).is_file() or not (inner / CLI_EXE).is_file():
            raise UpdateError(f"{zip_path.name} holds no {ZIP_FOLDER}/{APP_EXE}")
        inner.rename(new_dir)
    except (OSError, zipfile.BadZipFile) as ex:
        raise UpdateError(f"could not unpack {zip_path.name} next to {app_dir}: {ex}") from ex
    finally:
        shutil.rmtree(unpacking, ignore_errors=True)
    return PreparedUpdate(version, app_dir, new_dir)


def other_instances_running() -> bool:
    """True while another GUI or CLI process of the app runs, besides this one."""
    result = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, creationflags=_NO_WINDOW,
    )
    images = [line.split('","')[0].strip('"').lower() for line in result.stdout.splitlines()]
    return sum(image in (APP_EXE.lower(), CLI_EXE.lower()) for image in images) > 1


def start_swap(update: PreparedUpdate, restart_gui: bool) -> Path:
    """Write the swap helper next to the app and start it; the caller exits next.

    Returns the helper's path. The helper restarts the GUI when `restart_gui`.
    """
    paths = [str(update.app_dir), str(update.new_dir)]
    if any("%" in path or "!" in path for path in paths):
        raise UpdateError(f"the app folder {update.app_dir} has a % or ! in its path, which the update helper can't handle")
    helper = update.app_dir.parent / f"{update.app_dir.name}-update.cmd"
    helper.write_text(_helper_script(update, restart_gui), encoding="utf-8")
    subprocess.Popen(
        ["cmd.exe", "/c", str(helper)],
        cwd=update.app_dir.parent,
        creationflags=_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
    logging.info("Started %s to install %s", helper, update.version)
    return helper


# subprocess.CREATE_NO_WINDOW exists on Windows only; 0 keeps the import working elsewhere.
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _helper_script(update: PreparedUpdate, restart_gui: bool) -> str:
    app = update.app_dir
    return _HELPER_TEMPLATE.format(
        app=app,
        new=update.new_dir,
        old=app.parent / f"{app.name}.old",
        failed=app.parent / f"{app.name}.failed",
        data=PORTABLE_FOLDER,
        pid=os.getpid(),
        cli=CLI_EXE,
        restart=APP_EXE if restart_gui else "",
        log=Path(os.environ.get("TEMP", app.parent)) / "BDO-PAZ-Browser-update.log",
    ).replace("\n", "\r\n")


# Plain gotos, no ( ) blocks: cmd expands %VAR% in a block once, when it reads it.
# System tools by full path: another `find` (Git's) can come first on the PATH.
# Exit codes are compared as text: a PyInstaller exe that can't load Python
# exits with -1, which `if errorlevel 1` (1 or more) lets through.
_HELPER_TEMPLATE = r"""@echo off
setlocal
set "APP={app}"
set "NEW={new}"
set "OLD={old}"
set "FAILED={failed}"
set "LOG={log}"
set "RESTART={restart}"
set "SYS=%SystemRoot%\System32"
set TRIES=0
echo %DATE% %TIME% updating %APP% > "%LOG%"

:wait_for_app
"%SYS%\tasklist.exe" /FI "PID eq {pid}" /NH 2>nul | "%SYS%\find.exe" " {pid} " >nul
if errorlevel 1 goto app_closed
"%SYS%\ping.exe" -n 2 127.0.0.1 >nul
goto wait_for_app

:app_closed
if exist "%OLD%" rd /s /q "%OLD%"

:move_old
move "%APP%" "%OLD%" >nul 2>&1
if not errorlevel 1 goto old_moved
set /a TRIES+=1
if %TRIES% geq 30 goto give_up
"%SYS%\ping.exe" -n 2 127.0.0.1 >nul
goto move_old

:old_moved
echo moved the old version aside >> "%LOG%"
if exist "%OLD%\{data}" move "%OLD%\{data}" "%NEW%\{data}" >nul
move "%NEW%" "%APP%" >nul 2>&1
if not "%ERRORLEVEL%"=="0" goto roll_back
"%APP%\{cli}" --handlers >nul 2>&1
if not "%ERRORLEVEL%"=="0" goto roll_back
rd /s /q "%OLD%"
echo installed >> "%LOG%"
goto restart

:roll_back
echo the new version did not start, rolling back >> "%LOG%"
if exist "%FAILED%" rd /s /q "%FAILED%"
if exist "%APP%" move "%APP%" "%FAILED%" >nul
if exist "%FAILED%\{data}" move "%FAILED%\{data}" "%OLD%\{data}" >nul
if exist "%NEW%\{data}" move "%NEW%\{data}" "%OLD%\{data}" >nul
move "%OLD%" "%APP%" >nul
if exist "%FAILED%" rd /s /q "%FAILED%"
if exist "%NEW%" rd /s /q "%NEW%"
goto restart

:give_up
echo the app folder stayed locked, update skipped >> "%LOG%"
rd /s /q "%NEW%"

:restart
if not "%RESTART%"=="" start "" "%APP%\%RESTART%" --after-update
(goto) 2>nul & del "%~f0"
"""


def install_from_zip(zip_path: Path, current: str, restart_gui: bool) -> PreparedUpdate:
    """Check a downloaded release zip (with its `.sha256` next to it), unpack it, start the swap."""
    from app_version import parse_version

    version = version_of_zip(zip_path)
    if parse_version(version) <= parse_version(current):
        raise UpdateError(f"{zip_path.name} is v{version}, not newer than this v{current}")
    check_sha256(zip_path, read_sha256_file(zip_path.with_name(f"{zip_path.name}.sha256")))
    update = unpack(zip_path, version, running_app_dir())
    start_swap(update, restart_gui)
    return update
