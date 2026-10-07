"""`benchmark.py run | compare | profile`: repeatable decode timings."""
from __future__ import annotations

import argparse
import tempfile
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from pathlib import Path

from bdo_preview import BUNDLED_HANDLERS_DIR, load_plugins
from cli.errors import CliError
from cli.stdio import configure_logging, error, progress, use_utf8_stdio

from .compare import format_comparison
from .machine import describe_machine
from .pinning import UNPINNED, PinState, pin_process, running_cpu
from .profiling import profile_stage
from .report import describe_machine_line, describe_pin, format_timings
from .results import BenchResult, read_result, write_result
from .stages import (
    DEFAULT_ARCHIVE,
    DEFAULT_ENTRY,
    STAGE_NAMES,
    Workload,
    load_archive_workload,
    load_entry_workload,
    load_index_workload,
    load_folder_workload,
    load_loc_workload,
    parse_stage_names,
    select_stages,
)
from .timing import StageTiming, time_stage

REPO_ROOT = Path(__file__).resolve().parents[2]

# A fixed default, so two runs land on the same core. CPU 2 skips CPU 0, which
# serves most interrupts, and is a performance core on Intel hybrid CPUs.
DEFAULT_CPU = 2
DEFAULT_WARMUP = 1
DEFAULT_REPEATS = 5
DEFAULT_TOP = 100
_PROGRESS_EVERY = 10


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_plugins(BUNDLED_HANDLERS_DIR)
    use_utf8_stdio()
    configure_logging()
    try:
        return args.command(args)
    except CliError as ex:
        error(str(ex))
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="benchmark",
        description="Repeatable decode benchmarks, pinned to one CPU and saved with a machine fingerprint.",
    )
    commands = parser.add_subparsers(dest="command_name", required=True)

    run = commands.add_parser("run", help="Time the decode and parse stages of one PAZ entry or archive")
    _add_fixture_options(run)
    run.add_argument(
        "--repeats", metavar="N", type=_positive_int, default=DEFAULT_REPEATS,
        help=f"Timed runs per stage (default: {DEFAULT_REPEATS})",
    )
    run.add_argument(
        "--memory", action="store_true",
        help="Also measure each stage's peak memory, in one extra run that is many times slower",
    )
    run.add_argument("--output", metavar="FILE", type=Path, help="Save the result as JSON, for compare")
    run.set_defaults(command=run_benchmark)

    compare = commands.add_parser("compare", help="Compare two saved results, stage by stage")
    compare.add_argument("old", type=Path, help="The baseline result JSON")
    compare.add_argument("new", type=Path, help="The result JSON to compare against it")
    compare.set_defaults(command=run_compare)

    profile = commands.add_parser("profile", help="cProfile each stage once and print its hottest functions")
    _add_fixture_options(profile)
    profile.add_argument(
        "--top", metavar="N", type=_positive_int, default=DEFAULT_TOP,
        help=f"Functions to list per stage, by cumulative time (default: {DEFAULT_TOP})",
    )
    profile.add_argument(
        "--save", metavar="FILE", type=Path,
        help="Also write the .prof file (for snakeviz or pstats); needs one stage in --stages",
    )
    profile.set_defaults(command=run_profile)
    return parser


def _add_fixture_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--paz-folder", metavar="DIR", help="Path to the PAZ folder (default: last used)")
    workload = parser.add_mutually_exclusive_group()
    workload.add_argument(
        "--entry", metavar="FILE",
        help=f"Decode (and parse) one PAZ file: a path, name or pattern matching one file (default: {DEFAULT_ENTRY})",
    )
    workload.add_argument(
        "--archive", metavar="PAD", nargs="?", const=DEFAULT_ARCHIVE,
        help=f"Extract every file stored in one .paz archive, as extract_all does (default: {DEFAULT_ARCHIVE})",
    )
    workload.add_argument(
        "--index", action="store_true",
        help="Parse the client's file index (the .meta file and every archive's file table), as after a patch",
    )
    workload.add_argument(
        "--loc", metavar="LANG", nargs="?", const="",
        help="Build the LOC text index of one language, as every start does (default: the language picked in the app)",
    )
    workload.add_argument(
        "--folder", action="store_true",
        help="Load the folder's entry list from its cache and build the entry maps and the tree, as every start does",
    )
    parser.add_argument(
        "--stages", metavar="A,B",
        help=f"Only these stages, from {', '.join(STAGE_NAMES)} (default: every one the file has)",
    )
    parser.add_argument(
        "--warmup", metavar="N", type=_non_negative_int, default=DEFAULT_WARMUP,
        help=f"Untimed runs per stage first, to warm the file cache (default: {DEFAULT_WARMUP})",
    )
    pinning = parser.add_mutually_exclusive_group()
    pinning.add_argument(
        "--cpu", metavar="N", type=int, default=DEFAULT_CPU,
        help=f"Logical CPU to pin to; must be a performance core (default: {DEFAULT_CPU})",
    )
    pinning.add_argument(
        "--no-pin", action="store_true",
        help="Let the OS pick the core; the result is marked unpinned",
    )


def run_benchmark(args: argparse.Namespace) -> int:
    wanted = parse_stage_names(args.stages)
    pin = _pin(args)
    workload = _load_workload(args, wanted)
    machine = describe_machine(REPO_ROOT)
    progress(describe_machine_line(machine))

    timings: dict[str, StageTiming] = {}
    with tempfile.TemporaryDirectory(prefix="paz-bench-") as scratch:
        stages = select_stages(workload.build_stages(Path(scratch)), wanted, workload.info.name)
        for stage in stages:
            memory_note = ", then 1 memory run" if args.memory else ""
            progress(f"Timing {stage.name}: {args.warmup} warm-up, {args.repeats} timed{memory_note}…")
            timings[stage.name] = time_stage(
                stage.run,
                args.warmup,
                args.repeats,
                prepare=stage.prepare,
                with_gc=stage.with_gc,
                measure_memory=args.memory,
                on_run=_run_reporter(stage.name, args.repeats),
            )
    _check_still_pinned(pin)

    result = BenchResult(
        created=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        machine=machine,
        pin=pin,
        fixture=workload.info,
        warmup=args.warmup,
        repeats=args.repeats,
        stages=timings,
    )
    print(format_timings(result))
    if args.output is not None:
        write_result(args.output, result)
        progress(f"Saved to {args.output}")
    return 0


def run_compare(args: argparse.Namespace) -> int:
    print(format_comparison(read_result(args.old), read_result(args.new)))
    return 0


def run_profile(args: argparse.Namespace) -> int:
    wanted = parse_stage_names(args.stages)
    if args.save is not None and (wanted is None or len(wanted) != 1):
        raise CliError("--save needs exactly one stage in --stages, e.g. --stages decrypt.")
    pin = _pin(args)
    workload = _load_workload(args, wanted)
    with tempfile.TemporaryDirectory(prefix="paz-bench-") as scratch:
        for stage in select_stages(workload.build_stages(Path(scratch)), wanted, workload.info.name):
            progress(f"Profiling {stage.name}: {args.warmup} warm-up, then 1 profiled run…")
            for _ in range(args.warmup):
                if stage.prepare is not None:
                    stage.prepare()
                stage.run()
            print(f"== {stage.name} ==")
            print(profile_stage(stage, args.top, args.save))
    _check_still_pinned(pin)
    if args.save is not None:
        progress(f"Saved to {args.save}")
    return 0


def _load_workload(args: argparse.Namespace, wanted: Sequence[str] | None) -> Workload:
    if args.index:
        return load_index_workload(args.paz_folder)
    if args.folder:
        return load_folder_workload(args.paz_folder)
    if args.loc is not None:
        return load_loc_workload(args.paz_folder, args.loc or None)
    if args.archive is not None:
        return load_archive_workload(args.paz_folder, args.archive)
    return load_entry_workload(args.paz_folder, args.entry or DEFAULT_ENTRY, wanted)


def _pin(args: argparse.Namespace) -> PinState:
    pin = UNPINNED if args.no_pin else pin_process(args.cpu)
    progress(f"Pinning: {describe_pin(pin)}")
    return pin


def _run_reporter(stage_name: str, repeats: int) -> Callable[[int, float], None]:
    """Progress every `_PROGRESS_EVERY` runs, so a long run shows it is alive."""

    def report(number: int, seconds: float) -> None:
        if number % _PROGRESS_EVERY == 0 or number == repeats:
            progress(f"  {stage_name} {number}/{repeats}, last run {seconds:.3f}s")

    return report


def _check_still_pinned(pin: PinState) -> None:
    """Raise when the run ended on another core than the one it was pinned to."""
    cpu = running_cpu()
    if pin.is_pinned and cpu is not None and cpu != pin.cpu:
        raise CliError(f"pinned to CPU {pin.cpu} but finished on CPU {cpu}; the timings are not trustworthy.")


def _positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def _non_negative_int(text: str) -> int:
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError("must be 0 or more")
    return value
