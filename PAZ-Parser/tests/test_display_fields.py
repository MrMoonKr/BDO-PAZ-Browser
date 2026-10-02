"""Display-only record fields (`_` keys) stay out of search, sort and CSV; the
CLI record output keeps them."""
from __future__ import annotations

import json

from bdo_models import PazEntry
from bdo_preview import PreviewHandler
from cli.record_output import OutputFormat, format_records, record_fields
from record_export import records_to_csv
from table_sort import SORT_ASC, TableSort

_TAGGED = "<PAColor0xffe9bd23>Gold<PAOldColor>"
_RECORDS = [
    {"id": 1, "description": "Gold", "_description_pa": _TAGGED},
    {"id": 2, "description": "Plain", "_description_pa": "Plain"},
]


class _TaggedHandler(PreviewHandler):
    def get_records(self, data: bytes, entry: PazEntry, companions: dict[str, bytes]) -> list[dict]:
        return [dict(record) for record in _RECORDS]

    def render_records_page(self, records: list[dict], page: int, page_size: int) -> str:
        return ""


def _entry() -> PazEntry:
    return PazEntry(
        archive_name="test.paz",
        internal_path="tagged.dbss",
        offset=0,
        compressed_size=0,
        uncompressed_size=0,
        compression_type=0,
        encryption_type=0,
    )


def test_search_skips_display_fields() -> None:
    handler = _TaggedHandler()

    assert handler.search_records(b"x", _entry(), {}, "PAColor") == []
    assert handler.search_records(b"x", _entry(), {}, "gold") == [0]


def test_csv_leaves_display_fields_out() -> None:
    header = records_to_csv(_RECORDS).splitlines()[0]

    assert header == "id,description"
    assert "PAColor" not in records_to_csv(_RECORDS)


def test_display_field_never_sorts() -> None:
    assert TableSort.parse("_description_pa", SORT_ASC) is None
    assert TableSort.parse("description", SORT_ASC) == TableSort("description", SORT_ASC)


def test_cli_records_show_the_tagged_text() -> None:
    assert record_fields(_RECORDS) == ["id", "description", "_description_pa"]
    assert json.loads(format_records(_RECORDS, OutputFormat.JSON))[0]["_description_pa"] == _TAGGED
    assert "PAColor" not in format_records(_RECORDS, OutputFormat.CSV)
