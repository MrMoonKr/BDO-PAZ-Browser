"""How worker names and stats are shown: grade colors and in-game stat scales.

The files store stats as scaled integers. Divided by these scales they read as
the game's worker window shows them (a base Giant Worker: work speed 30.00,
move speed 2.00, luck 5.00).
Records keep the raw integers, so sorting and export stay exact.
"""

from __future__ import annotations

from _common.html import e
from .grade import WorkerGrade


WORK_SPEED_SCALE = 1_000_000
MOVE_SPEED_SCALE = 100
LUCK_SCALE = 10_000

_EMPTY = "-"


def format_stat(raw: int | None, scale: int) -> str:
    """A raw stat as the game shows it, with two decimals; a dash when missing."""
    if raw is None:
        return _EMPTY
    return f"{raw / scale:.2f}"


def worker_name_cell(name: str | None, grade: WorkerGrade | None) -> str:
    """The worker name in its in-game grade color; plain text without a grade."""
    if not name:
        return _EMPTY
    if grade is None:
        return e(name)
    return f'<span class="worker-grade-{grade.value}">{e(name)}</span>'
