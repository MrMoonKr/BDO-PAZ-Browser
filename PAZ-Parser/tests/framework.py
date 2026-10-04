from __future__ import annotations

from .case_input import CaseInput
from .declared import DeclaredCount, fixed_rows, header_count
from .models import HandlerCase, HandlerResult
from .runner import run_case
from .specs import DeclaredCountTest, PaFieldTest, RangeTest, SchemaTest, TargetTest, TestSpec, UserLanguageTest


def case_id(spec: object) -> str:
    if isinstance(spec, DeclaredCountTest):
        return "declared row count"
    if isinstance(spec, SchemaTest):
        return f"schema: {', '.join(spec.required_keys)}"
    if isinstance(spec, PaFieldTest):
        return f"{spec.field} keeps its game colours"
    if isinstance(spec, UserLanguageTest):
        return f"{', '.join(spec.fields)} in the user language"
    if isinstance(spec, RangeTest):
        return f"{spec.col} in [{spec.min_val}, {spec.max_val}]"
    if isinstance(spec, TargetTest):
        if isinstance(spec.value, (tuple, list, set, frozenset)):
            values = [str(item) for item in spec.value]
            if len(values) == 2:
                return f"{spec.col} in {values[0]}-{values[1]}"
            return f"{spec.col} in {', '.join(values)}"
        return f"{spec.col} = {spec.value}"
    return spec.__class__.__name__.lower()


__all__ = [
    "CaseInput",
    "DeclaredCount",
    "DeclaredCountTest",
    "HandlerCase",
    "HandlerResult",
    "PaFieldTest",
    "RangeTest",
    "SchemaTest",
    "TargetTest",
    "TestSpec",
    "UserLanguageTest",
    "case_id",
    "fixed_rows",
    "header_count",
    "run_case",
]
