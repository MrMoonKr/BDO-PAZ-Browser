from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping

from _common.lookup_index import IndexKind, LookupValue

from .case_input import CaseInput
from .specs import TestSpec


# An index, or a function that builds it when the case runs: an index built
# from other fixtures can't load at import time, where a missing client
# can't skip the test.
IndexSource = Mapping[int, LookupValue] | Callable[[], Mapping[int, LookupValue]]


@dataclass(frozen=True)
class HandlerCase:
    handler_name: str
    data_file: str | Path
    companion_files: Mapping[str, str | Path]
    loc_file: str | Path | None
    uses_loc: bool
    loc_fields: list[str]
    internal_path: str
    tests: list[TestSpec]
    record_mapper: Callable[[dict], dict] | None = None
    # Installed with init_index() while the handler runs, then removed.
    lookup_indexes: Mapping[IndexKind, IndexSource] = field(default_factory=dict)


@dataclass
class HandlerResult:
    row_count: int
    elapsed_ms: float
    loc_total_calls: int | None
    loc_fallback_count: int | None
    source: CaseInput = field(repr=False)
    records: list[dict] = field(default_factory=list, repr=False)
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    def check(self, spec: TestSpec) -> str:
        """Run `spec` against this result's records and the input they came from."""
        return spec.check(self.records, self.source)

    @property
    def status(self) -> str:
        return "passed" if not self.failed else "failed"

    @property
    def loc_summary(self) -> str:
        if self.loc_total_calls is None or self.loc_fallback_count is None:
            return "loc: disabled"

        return f"loc: {self.loc_fallback_count:,} misses / {self.loc_total_calls:,} lookups"

    def summary(self) -> str:
        return (
            f"{self.status}\n"
            f"  rows:  {self.row_count:,}\n"
            f"  parse: {self.elapsed_ms:.0f} ms\n"
            f"  {self.loc_summary}"
        )
