"""Read language JSON files the way the translation tests compare them."""
from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path

PLACEHOLDER = re.compile(r"\{(\w+)\}")


def flat_strings(path: Path) -> dict[str, str]:
    """Every text of a language file by dotted key, `_meta` left out."""
    def walk(node: dict, prefix: str) -> Iterator[tuple[str, str]]:
        for key, value in node.items():
            if isinstance(value, dict):
                yield from walk(value, f"{prefix}{key}.")
            elif isinstance(value, str):
                yield prefix + key, value

    data = json.loads(path.read_text(encoding="utf-8"))
    return dict(walk({k: v for k, v in data.items() if k != "_meta"}, ""))


def placeholders(text: str) -> set[str]:
    return set(PLACEHOLDER.findall(text))
