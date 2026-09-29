"""Load a PAZ folder headless, the way the GUI loads it."""
from __future__ import annotations

from pathlib import Path

from api.bdo_api import Api
from api.bdo_config import load_config
from bdo_models import PazEntry
from bdo_preview import set_handler_lang
from paz.bdo_paz_extract import parse_meta_file

from .errors import CliError
from .stdio import progress


def resolve_paz_root(paz_folder: str | None) -> Path:
    """The folder given, else the last one opened in the GUI."""
    folder = paz_folder or load_config().get("last_folder")
    if not folder:
        raise CliError("use --paz-folder or open a folder in the GUI first.")
    root = Path(folder)
    if not root.is_dir():
        raise CliError(f"PAZ folder not found: {root}")
    return root


def open_session(
    paz_folder: str | None,
    *,
    load_loc: bool = True,
    load_indexes: bool = True,
) -> Api:
    """An `Api` with the entry list loaded, plus LOC and lookup indexes if asked.

    LOC follows the language picked in the GUI settings, as in the app, and
    handlers render their labels in it.
    """
    paz_root = resolve_paz_root(paz_folder)
    set_handler_lang(load_config().get("language", "en"))

    extras = [name for name, wanted in (("LOC", load_loc), ("lookup indexes", load_indexes)) if wanted]
    progress("Loading PAZ entries" + (f", {' and '.join(extras)}" if extras else "") + "…")

    api = Api()
    try:
        msg = api.load_folder(
            paz_root,
            parse=_parse_announced,
            load_loc=load_loc,
            load_indexes=load_indexes,
        )
    except Exception as ex:
        raise CliError(f"cannot load PAZ folder {paz_root}: {ex}") from ex

    args = msg.get("args", {})
    progress(f"{args.get('count', '?')} entries, client version {args.get('version', '?')}.")
    return api


def _parse_announced(meta_path: Path) -> list[PazEntry]:
    progress("Parsing PAZ files (first run after a patch, this may take a while)…")
    return parse_meta_file(meta_path)
