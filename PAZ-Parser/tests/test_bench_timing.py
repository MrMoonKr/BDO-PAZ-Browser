"""bench.timing and the stage selection helpers of bench.stages."""
from __future__ import annotations

import pytest

from bench.stages import Stage, archive_file_name, parse_stage_names, select_stages
from bench.timing import StageTiming, time_stage
from cli.errors import CliError


class _Counter:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> None:
        self.calls += 1


def test_time_stage_runs_warmup_then_repeats_without_memory_by_default() -> None:
    run = _Counter()

    timing = time_stage(run, warmup=2, repeats=3)

    assert run.calls == 5
    assert len(timing.times_s) == 3
    assert timing.peak_bytes is None


def test_time_stage_adds_one_memory_run_when_asked() -> None:
    run = _Counter()

    timing = time_stage(run, warmup=0, repeats=1, measure_memory=True)

    assert run.calls == 2
    assert timing.peak_bytes is not None and timing.peak_bytes >= 0


def test_time_stage_reports_each_timed_run_in_order() -> None:
    seen: list[int] = []

    time_stage(lambda: None, warmup=1, repeats=3, on_run=lambda number, _seconds: seen.append(number))

    assert seen == [1, 2, 3]


@pytest.mark.parametrize(("warmup", "repeats"), [(-1, 1), (0, 0)])
def test_time_stage_rejects_impossible_run_counts(warmup: int, repeats: int) -> None:
    with pytest.raises(ValueError):
        time_stage(lambda: None, warmup=warmup, repeats=repeats)


def test_stage_timing_summaries() -> None:
    timing = StageTiming(times_s=(3.0, 1.0, 2.0), peak_bytes=None)

    assert timing.min_s == 1.0
    assert timing.median_s == 2.0
    assert timing.stdev_s == pytest.approx(1.0)
    assert StageTiming(times_s=(1.0,), peak_bytes=None).stdev_s == 0.0


def test_stage_timing_needs_a_run() -> None:
    with pytest.raises(ValueError):
        StageTiming(times_s=(), peak_bytes=None)


def test_parse_stage_names_accepts_a_comma_list_in_any_case() -> None:
    assert parse_stage_names(None) is None
    assert parse_stage_names(" Decrypt, read ") == ["decrypt", "read"]


@pytest.mark.parametrize("text", ["", "decrypt,unpack"])
def test_parse_stage_names_rejects_unknown_or_empty_lists(text: str) -> None:
    with pytest.raises(CliError):
        parse_stage_names(text)


_STAGES = [Stage("decrypt", lambda: None), Stage("read", lambda: None), Stage("extract", lambda: None)]


def test_select_stages_keeps_pipeline_order() -> None:
    picked = select_stages(_STAGES, ["extract", "decrypt"], "test.dds")

    assert [stage.name for stage in picked] == ["decrypt", "extract"]


def test_select_stages_names_a_stage_the_workload_lacks() -> None:
    with pytest.raises(CliError, match="no decompress stage"):
        select_stages(_STAGES, ["decompress"], "test.dds")


def test_archive_file_name_ignores_case_and_adds_the_extension() -> None:
    assert archive_file_name("PAD05889") == "pad05889.paz"
    assert archive_file_name(" pad05889.PAZ ") == "pad05889.paz"
