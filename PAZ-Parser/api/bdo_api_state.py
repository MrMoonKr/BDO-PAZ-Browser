from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import webview

from bdo_models import PazEntry
from bdo_preview import PreviewHandler
from paz.bdo_thumbnail_cache import ThumbnailCache
from table_sort import TableSort


class ApiState:
    """State and small helpers that `Api` and its mixins share.

    The mixins inherit this so every attribute they touch is declared in one
    place with its type.
    """

    def __init__(self, profile: bool = False, server: Any | None = None) -> None:
        self._profile = profile
        self._server = server
        self._window: webview.Window | None = None
        self._paz_root: Path | None = None
        self._entries: list[PazEntry] = []
        self._entry_map: dict[str, PazEntry] = {}
        self._entry_map_lower: dict[str, PazEntry] = {}
        self._icon_entry_cache: dict[str, PazEntry | None] = {}
        self._icon_data_url_cache: dict[str, str] = {}
        self._icon_decode_lock = threading.Lock()
        self._icon_preview_lock = threading.Lock()
        # norm path -> (decoded image, preview data URL), oldest first.
        self._icon_preview_images: dict[str, tuple[Any, str]] = {}
        self._thumbnail_cache: ThumbnailCache | None = None
        self._tree_data: dict = {}
        # "Show only handled tables": the tree, file search, global search
        # and extraction see only the entries a binary handler reads.
        self._handled_only = False
        # (handled entries, their tree), built on first use per folder load.
        self._handled_view: tuple[list[PazEntry], dict] | None = None
        self._disk_companions: dict[str, bytes] = {}
        self._status = "Open a PAZ folder to begin."
        self._cached_path: str | None = None
        self._cached_data: bytes | None = None
        self._cached_handler: PreviewHandler | None = None
        self._cached_entry: PazEntry | None = None
        self._cached_companions: dict[str, bytes] = {}
        self._cached_sort: TableSort | None = None
        self._global_search_cancel: threading.Event = threading.Event()

    def _ts(self) -> float:
        return time.perf_counter() if self._profile else 0.0

    def _te(self, profile: dict, key: str, start: float) -> None:
        if self._profile:
            profile[key] = (time.perf_counter() - start) * 1000

    def _push_js(self, js: str) -> None:
        if self._window is not None:
            try:
                self._window.evaluate_js(js)
            except Exception:
                pass

    def _push_status(self, msg: str | dict, progress: tuple[int, int] | None = None) -> None:
        self._status = msg if isinstance(msg, str) else msg.get("key", "")
        data: dict = msg if isinstance(msg, dict) else {"message": msg}
        data["progress"] = list(progress) if progress else None
        self._push_js(f"app.setStatus({json.dumps(data)})")

    if TYPE_CHECKING:
        # Implemented on Api; declared here so the mixins can call them.
        def read_entry(self, internal_path: str) -> bytes: ...

        def stream_url(self, internal_path: str) -> str: ...

        def _visible_entries(self) -> list[PazEntry]: ...

        def _load_companions_parallel(
            self, handler: PreviewHandler, entry: PazEntry
        ) -> dict[str, bytes]: ...
