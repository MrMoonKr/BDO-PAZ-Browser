from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CaseInput:
    """The bytes a case parsed: its data file and its companions by basename."""

    data: bytes
    companions: Mapping[str, bytes]

    def file(self, companion: str | None) -> bytes:
        """The data file when `companion` is None, else that companion."""
        if companion is None:
            return self.data
        if companion not in self.companions:
            raise AssertionError(f"case has no companion {companion!r}")
        return self.companions[companion]
