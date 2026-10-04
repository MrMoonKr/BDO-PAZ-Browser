"""Pin the benchmark process to one CPU at high priority, and prove it held.

The decode loops are pure Python, so they run on one core under the GIL and
pinning costs them nothing. It stops the OS moving the process between cores
mid-run: on a hybrid CPU an efficiency core runs them about 1.8x slower than a
performance core, which reads as a regression that is not there.

Windows pins and raises the priority; Linux pins only, since raising the
priority needs root. Other systems need `--no-pin`.
"""
from __future__ import annotations

import os
import struct
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from cli.errors import CliError

# One affinity mask covers processor group 0, 64 logical CPUs at most.
MAX_PINNABLE_CPU = 63

# The head of a SYSTEM_CPU_SET_INFORMATION record: Size, Type, Id, Group,
# LogicalProcessorIndex, CoreIndex, LastLevelCacheIndex, NumaNodeIndex,
# EfficiencyClass, AllFlags.
_CPU_SET_HEAD = struct.Struct("<IIIHBBBBBB")
_CPU_SET_INFORMATION = 0


@dataclass(frozen=True)
class CpuSet:
    """One logical CPU as Windows describes it."""

    group: int
    logical_index: int
    core_index: int
    # Higher is faster: performance cores outrank efficiency cores on a
    # hybrid CPU, and every CPU shares one class on any other.
    efficiency_class: int


@dataclass(frozen=True)
class PinState:
    """Where the benchmark ran, recorded in every result."""

    cpu: int | None
    efficiency_class: int | None
    top_efficiency_class: int | None
    is_high_priority: bool

    @property
    def is_pinned(self) -> bool:
        return self.cpu is not None


UNPINNED = PinState(cpu=None, efficiency_class=None, top_efficiency_class=None, is_high_priority=False)


def parse_cpu_sets(buffer: bytes) -> list[CpuSet]:
    """The CPU records of a GetSystemCpuSetInformation buffer."""
    sets: list[CpuSet] = []
    offset = 0
    while offset + _CPU_SET_HEAD.size <= len(buffer):
        size, kind, _id, group, logical, core, _cache, _numa, efficiency, _flags = (
            _CPU_SET_HEAD.unpack_from(buffer, offset)
        )
        if size < _CPU_SET_HEAD.size:
            raise ValueError(f"CPU set record at {offset} has size {size}")
        if kind == _CPU_SET_INFORMATION:
            sets.append(CpuSet(group, logical, core, efficiency))
        offset += size
    return sets


def efficiency_classes(sets: Iterable[CpuSet]) -> dict[int, int]:
    """Efficiency class by logical CPU number, for processor group 0."""
    return {cpu_set.logical_index: cpu_set.efficiency_class for cpu_set in sets if cpu_set.group == 0}


def format_cpu_list(cpus: Iterable[int]) -> str:
    """CPU numbers as compact ranges: [0, 1, 2, 5] -> "0-2, 5"."""
    ranges: list[tuple[int, int]] = []
    for cpu in sorted(set(cpus)):
        if ranges and cpu == ranges[-1][1] + 1:
            ranges[-1] = (ranges[-1][0], cpu)
        else:
            ranges.append((cpu, cpu))
    return ", ".join(str(first) if first == last else f"{first}-{last}" for first, last in ranges)


def check_performance_core(cpu: int, classes: Mapping[int, int]) -> None:
    """Raise when `cpu` is slower than the fastest cores of this machine."""
    if not classes:
        return
    top = max(classes.values())
    if classes.get(cpu, top) >= top:
        return
    fast = [number for number, efficiency in classes.items() if efficiency == top]
    raise CliError(
        f"CPU {cpu} is an efficiency core, about half as fast on this code. "
        f"Pick a performance core with --cpu: {format_cpu_list(fast)}."
    )


def check_cpu_number(cpu: int, cpu_count: int | None) -> None:
    if cpu < 0:
        raise CliError(f"--cpu must be 0 or more, got {cpu}.")
    if cpu > MAX_PINNABLE_CPU:
        raise CliError(f"--cpu must be at most {MAX_PINNABLE_CPU}, got {cpu}.")
    if cpu_count is not None and cpu >= cpu_count:
        raise CliError(f"this machine has CPUs 0-{cpu_count - 1}, got --cpu {cpu}.")


def pin_process(cpu: int) -> PinState:
    """Pin the whole process to logical CPU `cpu`, or raise if it does not hold."""
    check_cpu_number(cpu, os.cpu_count())
    if sys.platform == "win32":
        return _pin_windows(cpu)
    if sys.platform == "linux":
        return _pin_linux(cpu)
    raise CliError(f"pinning is not supported on {sys.platform}; run with --no-pin.")


def running_cpu() -> int | None:
    """The CPU the benchmark is on now, where the OS can say."""
    if sys.platform == "win32":
        from . import win32

        return win32.current_cpu()
    return None


def _pin_windows(cpu: int) -> PinState:
    from . import win32

    try:
        classes = efficiency_classes(parse_cpu_sets(win32.cpu_set_buffer()))
    except (OSError, ValueError):
        classes = {}
    check_performance_core(cpu, classes)

    try:
        win32.set_affinity(cpu)
        win32.set_high_priority()
    except OSError as ex:
        raise CliError(f"cannot pin to CPU {cpu}: {ex}") from ex
    if win32.affinity_mask() != 1 << cpu:
        raise CliError(f"the pin to CPU {cpu} did not hold; Windows reports another affinity mask.")

    return PinState(
        cpu=cpu,
        efficiency_class=classes.get(cpu),
        top_efficiency_class=max(classes.values()) if classes else None,
        is_high_priority=win32.is_high_priority(),
    )


def _pin_linux(cpu: int) -> PinState:
    if sys.platform != "linux":
        raise CliError("Linux pinning called on another system.")
    try:
        os.sched_setaffinity(0, {cpu})
    except OSError as ex:
        raise CliError(f"cannot pin to CPU {cpu}: {ex}") from ex
    if os.sched_getaffinity(0) != {cpu}:
        raise CliError(f"the pin to CPU {cpu} did not hold.")
    return PinState(cpu=cpu, efficiency_class=None, top_efficiency_class=None, is_high_priority=False)
