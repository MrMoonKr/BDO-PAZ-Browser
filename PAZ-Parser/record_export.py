"""Parsed records as CSV, shared by the GUI export and `browser.py --records --csv`."""
from __future__ import annotations

import csv
import io

from record_fields import data_fields


def records_to_csv(records: list[dict]) -> str:
    """CSV text with one column per key of the first record, in file order.

    Display-only fields (`_` keys) are left out. Empty when there are no
    records. Lines end in CRLF, the csv module default.
    """
    buf = io.StringIO()
    if records:
        writer = csv.DictWriter(buf, fieldnames=data_fields(records[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    return buf.getvalue()
