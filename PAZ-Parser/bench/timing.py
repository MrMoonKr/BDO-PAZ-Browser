"""Time one stage: warm-up runs, timed repeats, then an optional peak memory run."""
from __future__ import annotations

import gc
import statistics
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class StageTiming:
    times_s: tuple[float, ...]
    # None when the memory run was skipped.
    peak_bytes: int | None

    def __post_init__(self) -> None:
        if not self.times_s:
            raise ValueError("a stage timing needs at least one run")

    @property
    def min_s(self) -> float:
        # The least disturbed run, the steadiest figure for CPU-bound code.
        return min(self.times_s)

    @property
    def median_s(self) -> float:
        return statistics.median(self.times_s)

    @property
    def stdev_s(self) -> float:
        return statistics.stdev(self.times_s) if len(self.times_s) > 1 else 0.0


def time_stage(
    run: Callable[[], object],
    warmup: int,
    repeats: int,
    *,
    prepare: Callable[[], None] | None = None,
    with_gc: bool = False,
    measure_memory: bool = False,
    on_run: Callable[[int, float], None] | None = None,
) -> StageTiming:
    """Time `run` `repeats` times after `warmup` untimed calls.

    `prepare`, when given, runs untimed before every call of `run`, warm-up
    and memory run included. The garbage collector is off while timing, as in
    `timeit`, so a collection triggered by earlier allocations does not land
    in one run; `with_gc` keeps it on, for a stage whose collections are part
    of what the app pays. `on_run` gets the run number (from 1) and its time
    after each timed run.

    Peak memory comes from one more run under tracemalloc. It traces every
    allocation, which makes that run many times slower than a timed one, so it
    only happens when asked for and never shares a run with the timings.
    """
    if warmup < 0:
        raise ValueError(f"warmup must be 0 or more, got {warmup}")
    if repeats < 1:
        raise ValueError(f"repeats must be at least 1, got {repeats}")

    before_run = prepare or _nothing
    for _ in range(warmup):
        before_run()
        run()
    times: list[float] = []
    for number in range(1, repeats + 1):
        before_run()
        times.append(_timed_run(run, with_gc))
        if on_run is not None:
            on_run(number, times[-1])
    peak: int | None = None
    if measure_memory:
        before_run()
        peak = _peak_bytes(run)
    return StageTiming(times_s=tuple(times), peak_bytes=peak)


def _nothing() -> None:
    pass


def _timed_run(run: Callable[[], object], with_gc: bool) -> float:
    was_enabled = gc.isenabled()
    gc.collect()
    _set_gc(with_gc)
    try:
        start = time.perf_counter()
        # Held until the clock stops: freeing a parsed table's dicts is not
        # part of building them.
        result = run()
        elapsed = time.perf_counter() - start
    finally:
        _set_gc(was_enabled)
    del result
    return elapsed


def _set_gc(enabled: bool) -> None:
    if enabled:
        gc.enable()
    else:
        gc.disable()


def _peak_bytes(run: Callable[[], object]) -> int:
    tracemalloc.start()
    try:
        run()
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak
