"""The import boundary in `handler_api.py`: handler code reaches only what an exe bundles."""
from __future__ import annotations

import ast
import sys
from collections.abc import Iterator
from pathlib import Path

from handler_api import CORE_CALLED_COMMON, CORE_MODULES, STDLIB_MODULES

_PAZ_PARSER_DIR = Path(__file__).resolve().parents[1]
_HANDLERS_DIR = _PAZ_PARSER_DIR / "handlers"
# Handler packs ship without tests, so test modules may import anything.
_TEST_PREFIX = "test_"


def _handler_files() -> list[Path]:
    return sorted(
        path for path in _HANDLERS_DIR.rglob("*.py")
        if not path.name.startswith(_TEST_PREFIX) and "__pycache__" not in path.parts
    )


def _core_files() -> list[Path]:
    skipped = {_HANDLERS_DIR, _PAZ_PARSER_DIR / "tests"}
    return sorted(
        path for path in _PAZ_PARSER_DIR.rglob("*.py")
        if not any(folder in path.parents for folder in skipped)
        and path.name != "conftest.py"
        and "__pycache__" not in path.parts
    )


def _absolute_imports(path: Path) -> Iterator[tuple[int, str]]:
    """(line, module) for every absolute import in `path`, function-level ones too."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.lineno, node.module


def _handler_top_names() -> set[str]:
    """Names handler code imports itself by: top-level plugins and packages in `handlers/`."""
    return {
        path.stem if path.is_file() else path.name
        for path in _HANDLERS_DIR.iterdir()
        if (path.is_file() and path.suffix == ".py") or (path.is_dir() and path.name != "__pycache__")
    }


def test_handler_code_imports_only_what_the_exe_bundles() -> None:
    allowed = CORE_MODULES | STDLIB_MODULES | _handler_top_names()
    outside = [
        f"{path.relative_to(_PAZ_PARSER_DIR).as_posix()}:{line}: {module}"
        for path in _handler_files()
        for line, module in _absolute_imports(path)
        if module.split(".")[0] not in allowed
    ]
    assert outside == [], (
        "Handler code imports modules outside handler_api.py. Add them to an allowlist "
        "(a new exe and a HANDLER_API bump) or import something already on it:\n" + "\n".join(outside)
    )


def test_core_calls_only_the_listed_common_modules() -> None:
    called = {
        f"_common.{module.split('.')[1]}"
        for path in _core_files()
        for _, module in _absolute_imports(path)
        if module.startswith("_common.")
    }
    assert called - CORE_CALLED_COMMON == set(), "add them to CORE_CALLED_COMMON in handler_api.py"


def test_allowlists_name_real_modules() -> None:
    assert STDLIB_MODULES <= set(sys.stdlib_module_names)
    assert all((_PAZ_PARSER_DIR / f"{name}.py").is_file() for name in CORE_MODULES)
    assert all((_HANDLERS_DIR / f"{name.replace('.', '/')}.py").is_file() for name in CORE_CALLED_COMMON)
