"""cProfile one stage: where its time goes, not how long it takes.

The profiler slows every Python call, so these numbers are only good for
finding the hot functions. Timings to compare come from `run`.
"""
from __future__ import annotations

import cProfile
import io
import pstats
from pathlib import Path

from cli.errors import CliError

from .stages import Stage


def profile_stage(stage: Stage, top: int, save_to: Path | None = None) -> str:
    """The `top` entries of `stage` by cumulative time, as pstats prints them."""
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        stage.run()
    finally:
        profiler.disable()

    if save_to is not None:
        try:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            profiler.dump_stats(save_to)
        except OSError as ex:
            raise CliError(f"cannot write {save_to}: {ex}") from ex

    stream = io.StringIO()
    pstats.Stats(profiler, stream=stream).sort_stats(pstats.SortKey.CUMULATIVE).print_stats(top)
    return stream.getvalue()
