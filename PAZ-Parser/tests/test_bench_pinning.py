"""bench.pinning: CPU set parsing and the checks run before pinning."""
from __future__ import annotations

import struct

import pytest

from bench.pinning import (
    MAX_PINNABLE_CPU,
    CpuSet,
    check_cpu_number,
    check_performance_core,
    efficiency_classes,
    format_cpu_list,
    parse_cpu_sets,
)
from cli.errors import CliError

# A real SYSTEM_CPU_SET_INFORMATION record is 32 bytes; the parser reads the
# head and steps by the Size field.
_RECORD_SIZE = 32


def _record(logical: int, core: int, efficiency: int, group: int = 0, kind: int = 0) -> bytes:
    head = struct.pack("<IIIHBBBBBB", _RECORD_SIZE, kind, 256 + logical, group, logical, core, 0, 0, efficiency, 0)
    return head.ljust(_RECORD_SIZE, b"\x00")


def test_parse_cpu_sets_reads_each_record_by_its_size() -> None:
    buffer = _record(0, 0, 1) + _record(1, 0, 1) + _record(2, 1, 0)

    assert parse_cpu_sets(buffer) == [
        CpuSet(group=0, logical_index=0, core_index=0, efficiency_class=1),
        CpuSet(group=0, logical_index=1, core_index=0, efficiency_class=1),
        CpuSet(group=0, logical_index=2, core_index=1, efficiency_class=0),
    ]


def test_parse_cpu_sets_skips_records_of_another_type() -> None:
    assert parse_cpu_sets(_record(0, 0, 1, kind=1)) == []


def test_parse_cpu_sets_rejects_a_record_shorter_than_its_head() -> None:
    broken = struct.pack("<IIIHBBBBBB", 4, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    with pytest.raises(ValueError):
        parse_cpu_sets(broken)


def test_efficiency_classes_keep_processor_group_0_only() -> None:
    sets = [CpuSet(0, 0, 0, 1), CpuSet(1, 0, 0, 0)]

    assert efficiency_classes(sets) == {0: 1}


def test_format_cpu_list_joins_runs_into_ranges() -> None:
    assert format_cpu_list([5, 0, 2, 1, 7, 8]) == "0-2, 5, 7-8"
    assert format_cpu_list([3]) == "3"


def test_check_performance_core_names_the_fast_cores() -> None:
    hybrid = {0: 1, 1: 1, 2: 1, 3: 0}

    check_performance_core(2, hybrid)
    with pytest.raises(CliError, match="0-2"):
        check_performance_core(3, hybrid)


def test_check_performance_core_accepts_any_core_without_class_data() -> None:
    check_performance_core(5, {})


@pytest.mark.parametrize("cpu", [-1, MAX_PINNABLE_CPU + 1])
def test_check_cpu_number_rejects_cpus_outside_one_affinity_mask(cpu: int) -> None:
    with pytest.raises(CliError):
        check_cpu_number(cpu, cpu_count=None)


def test_check_cpu_number_rejects_a_cpu_the_machine_lacks() -> None:
    check_cpu_number(3, cpu_count=4)
    with pytest.raises(CliError, match="0-3"):
        check_cpu_number(4, cpu_count=4)
