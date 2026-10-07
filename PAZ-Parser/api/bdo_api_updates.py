"""App updates in the GUI: the start-up check behind the banner, and the one-click install."""

from __future__ import annotations

import html
import json
import logging
import threading
import webbrowser

from app_version import build_info
from ui_text import ui_text
from updates.install import fetch_release, other_instances_running, running_app_dir, start_swap, unpack
from updates.releases import RELEASES_PAGE, Release, UpdateError, newer_release

from .bdo_api_state import ApiState
from .bdo_config import check_app_updates_setting, load_config

# Links the UI may open in the system browser.
_OPENABLE_PREFIX = "https://github.com/iSayZes/BDO-PAZ-Browser"


def release_notes_html(notes: str) -> str:
    """The release notes as HTML: `### ` headings and `- ` items; everything escaped."""
    parts: list[str] = []
    items: list[str] = []

    def close_list() -> None:
        if items:
            parts.append("<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>")
            items.clear()

    for line in notes.splitlines():
        text = line.strip()
        if text.startswith("- "):
            items.append(html.escape(text[2:]))
            continue
        close_list()
        if text.startswith("#"):
            parts.append(f"<h4>{html.escape(text.lstrip('#').strip())}</h4>")
        elif text:
            parts.append(f"<p>{html.escape(text)}</p>")
    close_list()
    return "".join(parts)


class UpdateMixin(ApiState):
    def get_app_update(self) -> dict:
        """The newer release the banner offers, or {}.

        Only in the exe with "Check for updates on start" on; from source,
        `git pull` updates. A failed check is logged and shows nothing.
        """
        info = build_info()
        if info is None or not check_app_updates_setting(load_config()):
            return {}
        try:
            release = newer_release(info.version)
        except UpdateError:
            logging.warning("Update check failed", exc_info=True)
            return {}
        self._app_update = release
        if release is None:
            return {}
        return {
            "version": release.version,
            "current": info.version,
            "notes_html": release_notes_html(release.notes),
            "page_url": release.page_url,
        }

    def install_app_update(self) -> dict:
        """Download, check and unpack the offered release, then close for the swap.

        Returns at once; progress shows in the status bar and a failure in
        `app.onAppUpdateFailed(message)`.
        """
        release = self._app_update
        if release is None or build_info() is None:
            return {"ok": False, "error": ui_text("appUpdate.nothingToInstall")}
        if other_instances_running():
            return {"ok": False, "error": ui_text("appUpdate.otherInstances")}
        threading.Thread(target=self._install_app_update, args=(release,), daemon=True).start()
        return {"ok": True}

    def _install_app_update(self, release: Release) -> None:
        app_dir = running_app_dir()

        def progress(done: int, total: int) -> None:
            mb = f"{done / 1_048_576:.1f}"
            self._push_status({"key": "status.updateDownloading", "args": {"version": release.version, "mb": mb}},
                              (done, total) if total else None)

        try:
            zip_path = fetch_release(release, app_dir, progress)
            self._push_status({"key": "status.updateInstalling", "args": {"version": release.version}})
            update = unpack(zip_path, release.version, app_dir)
            zip_path.unlink(missing_ok=True)
            start_swap(update, restart_gui=True)
        except UpdateError as ex:
            logging.warning("Update to %s failed", release.version, exc_info=True)
            self._push_js(f"app.onAppUpdateFailed({json.dumps(str(ex))})")
            return
        if self._window is not None:
            self._window.destroy()

    def open_url(self, url: str) -> None:
        """Open a link of this project's GitHub page in the system browser."""
        if isinstance(url, str) and url.startswith(_OPENABLE_PREFIX):
            webbrowser.open(url)
        else:
            webbrowser.open(RELEASES_PAGE)
