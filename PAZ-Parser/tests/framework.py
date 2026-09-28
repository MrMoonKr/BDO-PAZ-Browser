from __future__ import annotations

from .case_input import CaseInput
from .declared import DeclaredCount, fixed_rows, header_count
from .models import HandlerCase, HandlerResult
from .runner import run_case
from .specs import CountTest, DeclaredCountTest, PosTest, RangeTest, SchemaTest, TargetTest, TestSpec


def case_id(spec: object) -> str:
    if isinstance(spec, DeclaredCountTest):
        return "declared row count"
    if isinstance(spec, CountTest):
        return "row count"
    if isinstance(spec, PosTest):
        return f"position = {spec.pos}"
    if isinstance(spec, SchemaTest):
        return f"schema: {', '.join(spec.required_keys)}"
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
    "CountTest",
    "DeclaredCount",
    "DeclaredCountTest",
    "HandlerCase",
    "HandlerResult",
    "PosTest",
    "RangeTest",
    "SchemaTest",
    "TargetTest",
    "TestSpec",
    "case_id",
    "fixed_rows",
    "header_count",
    "run_case",
]
