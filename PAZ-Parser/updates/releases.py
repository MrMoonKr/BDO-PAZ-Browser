"""The newest app release on GitHub, read from the releases API.

Releases are tags `v<date version>` with `BDO-PAZ-Browser-v<version>-windows.zip`
and its `.sha256`. The newest is picked by version, not by GitHub's "latest"
flag, so another release (such as a handler pack's) can never pass for it.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from dataclasses import dataclass

from app_version import parse_version

REPO = "iSayZes/BDO-PAZ-Browser"
# BDO_PAZ_RELEASES_URL tests the update flow without a GitHub release: a
# releases JSON in the API's shape, whose asset URLs may be file:// too.
RELEASES_URL = os.environ.get("BDO_PAZ_RELEASES_URL") or f"https://api.github.com/repos/{REPO}/releases?per_page=20"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"
ZIP_NAME = "BDO-PAZ-Browser-v{version}-windows.zip"
# Seconds; the GUI checks on start, so a slow network must not hold it up.
CHECK_TIMEOUT = 5


@dataclass(frozen=True)
class Release:
    version: str
    notes: str
    page_url: str
    zip_url: str
    sha256_url: str


class UpdateError(Exception):
    """An update step failed; the message says why, for the user."""


def newest_release(timeout: float = CHECK_TIMEOUT) -> Release | None:
    """The newest published app release, or None when there is none yet.

    Raises UpdateError when GitHub can't be reached or answers nonsense.
    """
    request = urllib.request.Request(
        RELEASES_URL,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "BDO-PAZ-Browser"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError) as ex:
        raise UpdateError(f"could not read the releases from GitHub: {ex}") from ex
    return newest_in(payload)


def newest_in(payload: object) -> Release | None:
    """The newest app release in a releases API answer, or None when it has none."""
    if not isinstance(payload, list):
        raise UpdateError("GitHub answered the releases request with something else")
    releases = [release for release in map(_parse_release, payload) if release is not None]
    return max(releases, key=lambda release: parse_version(release.version), default=None)


def newer_release(current: str, timeout: float = CHECK_TIMEOUT) -> Release | None:
    """The newest release when it is newer than `current`, else None."""
    release = newest_release(timeout)
    if release is None or parse_version(release.version) <= parse_version(current):
        return None
    return release


def _parse_release(item: object) -> Release | None:
    """A published app release with both assets, or None for anything else."""
    if not isinstance(item, dict) or item.get("draft") or item.get("prerelease"):
        return None
    tag = item.get("tag_name")
    if not isinstance(tag, str):
        return None
    try:
        parse_version(tag)
    except ValueError:
        return None
    version = tag.removeprefix("v")
    assets = {
        asset.get("name"): asset.get("browser_download_url")
        for asset in item.get("assets") or []
        if isinstance(asset, dict)
    }
    zip_name = ZIP_NAME.format(version=version)
    zip_url, sha256_url = assets.get(zip_name), assets.get(f"{zip_name}.sha256")
    if not isinstance(zip_url, str) or not isinstance(sha256_url, str):
        logging.info("Release %s has no %s with its .sha256; skipped", tag, zip_name)
        return None
    notes = item.get("body")
    page_url = item.get("html_url")
    return Release(
        version=version,
        notes=notes if isinstance(notes, str) else "",
        page_url=page_url if isinstance(page_url, str) else RELEASES_PAGE,
        zip_url=zip_url,
        sha256_url=sha256_url,
    )
