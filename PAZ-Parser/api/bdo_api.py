from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import webview

from .bdo_config import load_config, save_config, show_pa_tags_setting
from .bdo_api_helpers import _DISK_VIRTUAL_PREFIX, _file_icon, _norm, path_matcher
from .bdo_api_preview import PreviewMixin
from .bdo_api_search import SearchMixin
from paz.bdo_cache import load_cache, read_meta_version, save_cache
from paz.bdo_thumbnail_cache import ThumbnailCache
from paz.bdo_index_cache import load_index_cache, save_index_cache
from bdo_models import PazEntry
from paz.bdo_paz_extract import extract_entry, find_single_meta_file, parse_meta_file
from paz.bdo_payload_cache import cached_read_entry_payload, clear_payload_cache
from bdo_preview import StreamPreviewHandler, get_handler, set_handler_lang
from _common.pa_text import set_show_pa_tags

_COMPANION_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="companion")

_LOC_LANG_MAP: dict[str, tuple[str, ...] | None] = {
    "en": ("ads", "languagedata_en.loc"),
    "de": ("ads", "languagedata_de.loc"),
    "fr": ("ads", "languagedata_fr.loc"),
    "sp": ("ads", "languagedata_sp.loc"),
    "ru": ("ads", "languagedata_ru.loc"),
    "kr": None,
}
_VALID_LANGUAGES = frozenset(_LOC_LANG_MAP)
_DEFAULT_TABLE_ROW_HEIGHT = 27
_MIN_TABLE_ROW_HEIGHT = 20
_MAX_TABLE_ROW_HEIGHT = 64


def _count_entries(node: dict) -> int:
    total = 0
    for v in node.values():
        if isinstance(v, PazEntry):
            total += 1
        elif isinstance(v, dict):
            total += _count_entries(v)
    return total


def _table_row_height(value: object) -> int:
    if not isinstance(value, (int, float, str)):
        return _DEFAULT_TABLE_ROW_HEIGHT
    try:
        height = int(value)
    except ValueError:
        height = _DEFAULT_TABLE_ROW_HEIGHT
    return max(_MIN_TABLE_ROW_HEIGHT, min(_MAX_TABLE_ROW_HEIGHT, height))


class Api(PreviewMixin, SearchMixin):
    """Backend the UI calls through pywebview; the CLI loads folders through it too."""

    @property
    def entries(self) -> list[PazEntry]:
        """Every entry of the loaded folder, in meta file order."""
        return self._entries

    @property
    def paz_root(self) -> Path | None:
        return self._paz_root

    def set_window(self, window: webview.Window) -> None:
        self._window = window
        cfg = load_config()
        set_handler_lang(cfg.get("language", "en"))
        set_show_pa_tags(show_pa_tags_setting(cfg))

    # ── Folder ────────────────────────────────────────────────────────────────

    def open_folder(self) -> dict:
        if self._window is None:
            return {"ok": False, "error": "Window not initialized"}
        result = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        if not result:
            return {"ok": False}
        self._paz_root = Path(result[0])
        save_config({"last_folder": str(self._paz_root)})
        threading.Thread(target=self._load_entries, daemon=True).start()
        return {"ok": True, "path": str(self._paz_root)}

    def get_last_folder(self) -> dict:
        path = load_config().get("last_folder")
        if path and Path(path).is_dir():
            return {"path": path}
        return {}

    def open_folder_path(self, path: str) -> dict:
        p = Path(path)
        if not p.is_dir():
            return {"ok": False, "error": "Folder not found"}
        self._paz_root = p
        threading.Thread(target=self._load_entries, daemon=True).start()
        return {"ok": True, "path": str(self._paz_root)}

    def browse_folder(self) -> dict:
        """Open a folder picker without side effects, for use in the settings modal."""
        if self._window is None:
            return {"ok": False, "error": "Window not initialized"}
        result = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        if not result:
            return {"ok": False}
        return {"ok": True, "path": str(Path(result[0]))}

    # ── Settings ──────────────────────────────────────────────────────────────

    def get_settings(self) -> dict:
        cfg = load_config()
        return {
            "paz_path": cfg.get("last_folder", ""),
            "language": cfg.get("language", "en"),
            "table_row_height": _table_row_height(cfg.get("table_row_height")),
            "show_pa_tags": show_pa_tags_setting(cfg),
        }

    def save_settings(
        self,
        paz_path: str,
        language: str,
        table_row_height: int | None = None,
        show_pa_tags: bool = False,
    ) -> dict:
        if language not in _VALID_LANGUAGES:
            return {"ok": False, "error": f"Invalid language: {language}"}
        old_cfg = load_config()
        row_height = _table_row_height(table_row_height)
        save_config({
            "last_folder": paz_path,
            "language": language,
            "table_row_height": row_height,
            "show_pa_tags": show_pa_tags is True,
        })
        set_show_pa_tags(show_pa_tags is True)
        self._reload_loc(language)
        if paz_path != old_cfg.get("last_folder", "") and Path(paz_path).is_dir():
            self._paz_root = Path(paz_path)
            threading.Thread(target=self._load_entries, daemon=True).start()
        return {"ok": True, "table_row_height": row_height}

    def _reload_loc(self, language: str) -> None:
        from _common.loc import init_loc  # noqa: PLC0415
        set_handler_lang(language)
        rel = _LOC_LANG_MAP.get(language)
        if rel is None or not self._paz_root:
            init_loc(None)
            return
        path = self._paz_root.parent.joinpath(*rel)
        if path.exists():
            try:
                init_loc(path.read_bytes())
            except Exception:
                pass
        else:
            init_loc(None)

    def _load_entries(self) -> None:
        assert self._paz_root is not None
        try:
            msg = self.load_folder(self._paz_root, parse=self._parse_with_ticker)
            self._push_status(msg)
            self._push_js("app.onFolderLoaded()")

        except Exception as ex:
            self._push_status({"key": "status.error", "args": {"message": str(ex)}})
            self._push_js(f"app.showError({json.dumps(str(ex))})")

    def load_folder(
        self,
        paz_root: Path,
        *,
        parse: Callable[[Path], list[PazEntry]] = parse_meta_file,
        load_loc: bool = True,
        load_indexes: bool = True,
    ) -> dict:
        """Load the entry list, LOC and lookup indexes of `paz_root`, blocking.

        The GUI runs this on a worker thread; the CLI calls it directly, so a
        command sees the same data the app shows. `parse` reads the meta file
        when the entry cache is stale. Raises when the folder cannot be read,
        and returns the status message to show.
        """
        self._paz_root = paz_root
        clear_payload_cache()
        meta_path = find_single_meta_file(paz_root)
        current_version = read_meta_version(meta_path)
        cached = load_cache(paz_root)

        if cached and cached[0] == current_version:
            _, entries = cached
            msg = {"key": "status.loadedFromCache", "args": {"count": f"{len(entries):,}", "version": current_version}}
        else:
            entries = parse(meta_path)
            save_cache(paz_root, current_version, entries)
            msg = {"key": "status.parsedAndCached", "args": {"count": f"{len(entries):,}", "version": current_version}}

        self._entries = entries
        self._entry_map = {_norm(e.internal_path): e for e in entries}
        self._entry_map_lower = {path.lower(): entry for path, entry in self._entry_map.items()}
        self._icon_entry_cache.clear()
        self._icon_data_url_cache.clear()
        self._icon_preview_images.clear()
        self._open_thumbnail_cache(paz_root, current_version)
        self._tree_data = self._build_tree_data(entries)
        self._disk_companions = {}
        if load_loc:
            self._load_disk_companions()
        if load_indexes:
            self._load_lookup_indexes(current_version)
        return msg

    def _open_thumbnail_cache(self, paz_root: Path, meta_version: int) -> None:
        if self._thumbnail_cache is not None:
            self._thumbnail_cache.close()
        self._thumbnail_cache = ThumbnailCache(paz_root, meta_version)

    def _parse_with_ticker(self, meta_path: Path) -> list[PazEntry]:
        """Parse the meta file while pushing the elapsed time to the status bar."""
        stop_ticker = threading.Event()
        start = time.monotonic()

        def _ticker(stop: threading.Event, t0: float) -> None:
            while not stop.is_set():
                elapsed = int(time.monotonic() - t0)
                self._push_status(
                    {"key": "status.parsing", "args": {"elapsed": elapsed}}
                )
                stop.wait(0.5)

        threading.Thread(target=_ticker, args=(stop_ticker, start), daemon=True).start()
        try:
            return parse_meta_file(meta_path)
        finally:
            stop_ticker.set()

    def _load_lookup_indexes(self, version: int) -> None:
        """Install every lookup index, from cache or by building it.

        Icons whose file is named after a 3D asset, or filed under a
        per-category folder, cannot be reached from an entity ID, so an index
        is the only way to show them. A failure here is not fatal: icon kinds
        that declare a derivation still fall back to it, and other handlers
        show a dash.
        """
        from _common.lookup_index import IndexKind, clear_indexes, init_index  # noqa: PLC0415
        from .bdo_lookup_indexes import build_indexes, index_fingerprint  # noqa: PLC0415

        if not self._paz_root:
            return

        clear_indexes()
        by_value = {kind.value: kind for kind in IndexKind}
        fingerprint = index_fingerprint()

        cached = load_index_cache(self._paz_root, fingerprint)
        if cached and cached[0] == version:
            indexes = cached[1]
        else:
            try:
                indexes = build_indexes(
                    self._load_companion_sync, self._entry_map_lower.__contains__
                )
            except Exception as ex:
                logging.warning("Could not build the lookup indexes", exc_info=True)
                self._push_status(
                    {"key": "status.indexFailed", "args": {"message": str(ex)}}
                )
                return

            if indexes:
                try:
                    save_index_cache(self._paz_root, version, fingerprint, indexes)
                except Exception:
                    # Not fatal: the indexes are installed below, only the next
                    # launch has to build them again.
                    logging.warning(
                        "Could not write the lookup index cache in %s",
                        self._paz_root,
                        exc_info=True,
                    )

        for name, mapping in indexes.items():
            kind = by_value.get(name)
            if kind is not None:
                init_index(kind, mapping)

    def _load_disk_companions(self) -> None:
        if not self._paz_root:
            return
        language = load_config().get("language", "en")
        rel = _LOC_LANG_MAP.get(language)
        if rel is not None:
            path = self._paz_root.parent.joinpath(*rel)
            if path.exists():
                try:
                    raw = path.read_bytes()
                    self._disk_companions[rel[-1]] = raw
                    from _common.loc import init_loc  # noqa: PLC0415
                    init_loc(raw)
                except Exception:
                    # Not fatal: tables fall back to their inline text.
                    logging.warning("Could not load LOC file %s", path, exc_info=True)

    def _load_companion_sync(self, internal_path: str) -> bytes | None:
        entry = self._entry_map.get(_norm(internal_path))
        if not entry or not self._paz_root:
            return None
        try:
            return cached_read_entry_payload(
                archive_path=self._paz_root / entry.archive_name,
                entry=entry,
            )
        except Exception:
            return None

    def _load_companions_parallel(self, handler, entry: PazEntry) -> dict[str, bytes]:
        paths = handler.companions(entry)
        if not paths:
            return {}
        if len(paths) == 1:
            raw = self._load_companion_sync(paths[0])
            return {Path(paths[0]).name: raw} if raw is not None else {}
        futures = {_COMPANION_POOL.submit(self._load_companion_sync, cp): cp for cp in paths}
        result: dict[str, bytes] = {}
        for future in as_completed(futures):
            cp = futures[future]
            try:
                raw = future.result()
            except Exception:
                raw = None
            if raw is not None:
                result[Path(cp).name] = raw
        return result

    def get_entry(self, internal_path: str) -> PazEntry | None:
        return self._entry_map.get(_norm(internal_path))

    def read_entry(self, internal_path: str) -> bytes:
        entry = self.get_entry(internal_path)
        if not entry or not self._paz_root:
            raise FileNotFoundError(internal_path)
        return cached_read_entry_payload(
            archive_path=self._paz_root / entry.archive_name,
            entry=entry,
        )

    def get_stream_mime_type(self, internal_path: str) -> str:
        p = Path(internal_path)
        handler = get_handler(p.name, p.suffix)
        if isinstance(handler, StreamPreviewHandler):
            return handler.mime_type
        return "application/octet-stream"

    def is_streamable(self, internal_path: str) -> bool:
        p = Path(internal_path)
        return isinstance(get_handler(p.name, p.suffix), StreamPreviewHandler)

    def stream_url(self, internal_path: str) -> str:
        if self._server is None:
            raise RuntimeError("Local stream server not available")
        return self._server.stream_url(_norm(internal_path))

    def get_server_info(self) -> dict:
        if self._server is None:
            return {}
        return {"port": self._server.port, "token": self._server.token}

    # ── Tree ──────────────────────────────────────────────────────────────────

    def _build_tree_data(self, entries: list[PazEntry]) -> dict:
        root: dict = {}
        for entry in entries:
            parts = _norm(entry.internal_path).split("/")
            node = root
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = entry
        return root

    def get_children(self, node_path: str) -> list[dict]:
        """Return immediate children of a tree node for lazy loading."""
        node: Any = self._tree_data
        if node_path:
            for part in node_path.split("/"):
                if isinstance(node, dict):
                    node = node.get(part, {})
                else:
                    return []

        if not isinstance(node, dict):
            return []

        dirs  = sorted((k, v) for k, v in node.items() if isinstance(v, dict))
        files = sorted((k, v) for k, v in node.items() if isinstance(v, PazEntry))

        result: list[dict] = []

        if not node_path:
            for name in sorted(self._disk_companions):
                result.append({
                    "id":   f"{_DISK_VIRTUAL_PREFIX}/{name}",
                    "name": name,
                    "type": "file",
                    "icon": _file_icon(Path(name).suffix),
                    "disk": True,
                })

        for name, child_node in dirs:
            child_path = f"{node_path}/{name}" if node_path else name
            result.append({
                "id":          child_path,
                "name":        name,
                "type":        "dir",
                "count":       _count_entries(child_node),
                "icon":        "📁",
                "has_children": bool(child_node),
            })
        for name, entry in files:
            result.append({
                "id":   _norm(entry.internal_path),
                "name": name,
                "type": "file",
                "icon": _file_icon(Path(name).suffix),
            })
        return result

    def search(self, query: str) -> list[dict]:
        """Return up to 500 entries matching `query`.

        Glob patterns (containing *, ?, or [) are matched against the full
        path and against the filename alone.  Plain strings do substring match.
        """
        is_hit = path_matcher(query)
        results: list[dict] = []
        for entry in self._entries:
            path = _norm(entry.internal_path)
            name = path.rsplit("/", 1)[-1]
            if is_hit(path):
                results.append({
                    "id":   path,
                    "name": name,
                    "path": path,
                    "icon": _file_icon(Path(name).suffix),
                })
                if len(results) == 500:
                    break
        return results

    # ── Extraction ────────────────────────────────────────────────────────────

    def pick_output_folder(self) -> str | None:
        if self._window is None:
            return None
        result = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        return result[0] if result else None

    def extract_entries(self, paths: list[str], output_dir: str) -> dict:
        if not self._paz_root:
            return {"error": "No PAZ folder loaded"}

        entries: list[PazEntry] = []
        seen: set[str] = set()

        for path in paths:
            path = _norm(path)
            if path in self._entry_map:
                if path not in seen:
                    seen.add(path)
                    entries.append(self._entry_map[path])
            else:
                node: Any = self._tree_data
                for part in path.split("/"):
                    node = node.get(part, {}) if isinstance(node, dict) else {}
                collect: list[PazEntry] = []
                self._collect_recursive(node, collect)
                for e in collect:
                    ep = _norm(e.internal_path)
                    if ep not in seen:
                        seen.add(ep)
                        entries.append(e)

        if not entries:
            return {"error": "No entries to extract"}

        paz_root    = self._paz_root
        output_root = Path(output_dir)
        total       = len(entries)

        def run() -> None:
            extracted = skipped = failed = 0
            for i, entry in enumerate(entries, 1):
                try:
                    result = extract_entry(
                        paz_root=paz_root, output_root=output_root,
                        entry=entry, overwrite=False,
                    )
                    if result == "skipped":
                        skipped += 1
                    else:
                        extracted += 1
                except Exception:
                    failed += 1

                if i % 25 == 0 or i == total:
                    self._push_status(
                        {"key": "status.extracting", "args": {"done": i, "total": total, "extracted": extracted, "skipped": skipped, "failed": failed}},
                        (i, total),
                    )

            self._push_status({"key": "status.extractDone", "args": {"extracted": extracted, "skipped": skipped, "failed": failed}})
            self._push_js("app.onExtractionDone()")

        threading.Thread(target=run, daemon=True).start()
        return {"total": total}

    def _collect_recursive(self, node: Any, out: list[PazEntry]) -> None:
        if isinstance(node, PazEntry):
            out.append(node)
        elif isinstance(node, dict):
            for v in node.values():
                self._collect_recursive(v, out)

    def get_selection_size(self, paths: list[str]) -> dict:
        seen: set[str] = set()
        total_bytes = 0

        for path in paths:
            path = _norm(path)
            if path in self._entry_map:
                if path not in seen:
                    seen.add(path)
                    total_bytes += self._entry_map[path].uncompressed_size
            else:
                node: Any = self._tree_data
                for part in path.split("/"):
                    node = node.get(part, {}) if isinstance(node, dict) else {}
                entries: list[PazEntry] = []
                self._collect_recursive(node, entries)
                for e in entries:
                    ep = _norm(e.internal_path)
                    if ep not in seen:
                        seen.add(ep)
                        total_bytes += e.uncompressed_size

        return {"count": len(seen), "bytes": total_bytes}

    # ── Plugins ───────────────────────────────────────────────────────────────

    def reload_plugins(self) -> None:
        import bdo_preview
        bdo_preview.reload_plugins(Path(__file__).parent.parent / "handlers")
        self._reload_loc(load_config().get("language", "en"))
        self._push_js("app.onPluginsReloaded()")

    # ── Status ────────────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        return {"message": self._status, "progress": None}
