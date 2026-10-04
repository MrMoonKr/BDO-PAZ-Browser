"""The fixture cases of every handler, for tests that run over all handlers."""
from __future__ import annotations

import importlib
from pathlib import Path

from .models import HandlerCase

_HANDLERS_DIR = Path(__file__).resolve().parent.parent / "handlers"


def handler_cases() -> list[HandlerCase]:
    """Every module-level HandlerCase in the handler-local test modules, one per file."""
    cases: dict[str, HandlerCase] = {}
    for path in sorted(_HANDLERS_DIR.glob("*/*/test_*.py")):
        module_name = ".".join(path.relative_to(_HANDLERS_DIR).with_suffix("").parts)
        module = importlib.import_module(module_name)
        for value in vars(module).values():
            if isinstance(value, HandlerCase):
                cases.setdefault(value.internal_path, value)
    return list(cases.values())


def case_file_name(case: HandlerCase) -> str:
    """The case's file name, as a pytest parameter id."""
    return Path(case.internal_path).name
