from __future__ import annotations

from pathlib import Path

from _common.offset_table import (
    OffsetColumn,
    OffsetTableHandler,
    offset_column,
    offset_map_records,
)


_LANG_DIR = Path(__file__).parent / "lang"


def title_offset_handler() -> OffsetTableHandler:
    return OffsetTableHandler(
        _LANG_DIR,
        [
            OffsetColumn("title_id", "titleId", "Title ID"),
            offset_column("offset", "offset", "Offset"),
        ],
        offset_map_records("title_id"),
        lang_block="columns",
    )
