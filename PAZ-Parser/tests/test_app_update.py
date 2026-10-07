"""App updates: picking the release, checking and unpacking its zip, the swap helper."""
from __future__ import annotations

import hashlib
import http.server
import threading
import zipfile
from collections.abc import Iterator
from functools import partial
from pathlib import Path

import pytest

from api.bdo_api_updates import release_notes_html
from api.bdo_config import check_app_updates_setting
from updates.install import (
    APP_EXE,
    CLI_EXE,
    ZIP_FOLDER,
    PreparedUpdate,
    check_sha256,
    download,
    read_sha256_file,
    start_swap,
    unpack,
    version_of_zip,
    _helper_script,
)
from updates.releases import UpdateError, newest_in


def _release_item(tag: str, **extra: object) -> dict:
    name = f"BDO-PAZ-Browser-{tag}-windows.zip"
    return {
        "tag_name": tag,
        "html_url": f"https://github.com/iSayZes/BDO-PAZ-Browser/releases/tag/{tag}",
        "body": "### New\n\n- feat: something",
        "assets": [
            {"name": name, "browser_download_url": f"https://example.invalid/{name}"},
            {"name": f"{name}.sha256", "browser_download_url": f"https://example.invalid/{name}.sha256"},
        ],
        **extra,
    }


# ── Picking the release ──────────────────────────────────────────────────────

def test_the_newest_release_is_picked_by_version_not_by_order() -> None:
    payload = [_release_item("v2026.10.07"), _release_item("v2026.10.12"), _release_item("v2026.10.07.2")]

    release = newest_in(payload)

    assert release is not None and release.version == "2026.10.12"
    assert release.zip_url.endswith("BDO-PAZ-Browser-v2026.10.12-windows.zip")


def test_drafts_prereleases_other_tags_and_releases_without_the_zip_are_skipped() -> None:
    payload = [
        _release_item("v2026.12.01", draft=True),
        _release_item("v2026.12.02", prerelease=True),
        {**_release_item("handlers-latest")},
        {**_release_item("v2026.12.03"), "assets": []},
        _release_item("v2026.10.07"),
    ]

    release = newest_in(payload)

    assert release is not None and release.version == "2026.10.07"


def test_no_release_yet_is_none() -> None:
    assert newest_in([]) is None


def test_an_answer_that_is_not_a_list_is_an_error() -> None:
    with pytest.raises(UpdateError):
        newest_in({"message": "API rate limit exceeded"})


def test_release_notes_become_escaped_html() -> None:
    notes = "### New\n\n- feat: <b>bold</b> & more\n- fix: x\n\n+3 more changes: https://github.com/x"

    assert release_notes_html(notes) == (
        "<h4>New</h4><ul><li>feat: &lt;b&gt;bold&lt;/b&gt; &amp; more</li><li>fix: x</li></ul>"
        "<p>+3 more changes: https://github.com/x</p>"
    )


def test_the_update_check_is_on_unless_turned_off() -> None:
    assert check_app_updates_setting({}) is True
    assert check_app_updates_setting({"check_app_updates": False}) is False


# ── The zip ──────────────────────────────────────────────────────────────────

def _release_zip(folder: Path, version: str, files: dict[str, bytes] | None = None) -> Path:
    zip_path = folder / f"BDO-PAZ-Browser-v{version}-windows.zip"
    content = files if files is not None else {APP_EXE: b"gui", CLI_EXE: b"cli", "_internal/x.dll": b"dll"}
    with zipfile.ZipFile(zip_path, "w") as archive:
        for name, data in content.items():
            archive.writestr(f"{ZIP_FOLDER}/{name}", data)
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    zip_path.with_name(f"{zip_path.name}.sha256").write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
    return zip_path


def test_the_version_comes_from_the_zip_name(tmp_path: Path) -> None:
    assert version_of_zip(tmp_path / "BDO-PAZ-Browser-v2026.10.07.2-windows.zip") == "2026.10.07.2"
    with pytest.raises(UpdateError):
        version_of_zip(tmp_path / "BDO-PAZ-Browser.zip")


def test_a_matching_hash_passes_and_a_broken_zip_does_not(tmp_path: Path) -> None:
    zip_path = _release_zip(tmp_path, "2026.10.12")
    expected = read_sha256_file(zip_path.with_name(f"{zip_path.name}.sha256"))

    check_sha256(zip_path, expected)
    with zip_path.open("ab") as file:
        file.write(b"x")
    with pytest.raises(UpdateError):
        check_sha256(zip_path, expected)


def test_unpacking_puts_the_new_version_next_to_the_app(tmp_path: Path) -> None:
    app_dir = tmp_path / "BDO-PAZ-Browser"
    app_dir.mkdir()
    zip_path = _release_zip(tmp_path, "2026.10.12")

    update = unpack(zip_path, "2026.10.12", app_dir)

    assert update.new_dir == tmp_path / "BDO-PAZ-Browser.new"
    assert (update.new_dir / APP_EXE).read_bytes() == b"gui"
    assert (update.new_dir / "_internal" / "x.dll").is_file()
    assert not (tmp_path / "BDO-PAZ-Browser.unpacking").exists()


def test_a_zip_without_the_exes_is_refused(tmp_path: Path) -> None:
    app_dir = tmp_path / "BDO-PAZ-Browser"
    app_dir.mkdir()
    zip_path = _release_zip(tmp_path, "2026.10.12", {"readme.txt": b"no exe here"})

    with pytest.raises(UpdateError):
        unpack(zip_path, "2026.10.12", app_dir)
    assert not (tmp_path / "BDO-PAZ-Browser.new").exists()


@pytest.fixture
def file_server(tmp_path: Path) -> Iterator[tuple[str, Path]]:
    """An HTTP server for `tmp_path/served`; yields its base URL and the folder."""
    served = tmp_path / "served"
    served.mkdir()
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(served))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}", served
    server.shutdown()


def test_download_writes_the_file_and_reports_progress(file_server: tuple[str, Path], tmp_path: Path) -> None:
    base, served = file_server
    (served / "asset.bin").write_bytes(b"a" * 300_000)
    reports: list[tuple[int, int]] = []

    download(f"{base}/asset.bin", tmp_path / "asset.bin", lambda done, total: reports.append((done, total)))

    assert (tmp_path / "asset.bin").read_bytes() == b"a" * 300_000
    assert reports[-1] == (300_000, 300_000)


def test_a_failed_download_leaves_nothing_behind(file_server: tuple[str, Path], tmp_path: Path) -> None:
    base, _ = file_server

    with pytest.raises(UpdateError):
        download(f"{base}/missing.bin", tmp_path / "missing.bin")
    assert list(tmp_path.glob("missing.bin*")) == []


# ── The swap helper ──────────────────────────────────────────────────────────

def test_the_helper_carries_the_data_folder_over_and_checks_the_new_cli(tmp_path: Path) -> None:
    update = PreparedUpdate("2026.10.12", tmp_path / "BDO-PAZ-Browser", tmp_path / "BDO-PAZ-Browser.new")

    script = _helper_script(update, restart_gui=True)

    assert "\r\n" in script
    assert f'set "APP={tmp_path / "BDO-PAZ-Browser"}"' in script
    assert 'move "%OLD%\\data" "%NEW%\\data"' in script
    assert f'"%APP%\\{CLI_EXE}" --handlers' in script
    assert f'set "RESTART={APP_EXE}"' in script
    assert 'set "RESTART="' in _helper_script(update, restart_gui=False)


def test_a_path_cmd_cannot_quote_is_refused(tmp_path: Path) -> None:
    update = PreparedUpdate("2026.10.12", tmp_path / "100%" / "app", tmp_path / "100%" / "app.new")

    with pytest.raises(UpdateError):
        start_swap(update, restart_gui=False)
