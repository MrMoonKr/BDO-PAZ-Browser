"""Plantation workers: grade, name color and stat scales, shared by the worker tables.

Grade comes from `plantworker.bss` `grade_class` (`+0x06`), one value per grade:
28023 base, 28024 Skilled, 28025 Professional, 28026 Artisan and 28027 for
named workers such as Acher. Naive workers share 28023 with base workers, so
inside that class the English name decides ("Naive ..."). A few workers are
white whatever their class and are listed by ID. All of it was checked against
the in-game name colors on 2026-09-28.

The files store stats as scaled integers. Divided by these scales they read as
the game's worker window shows them (a base Giant Worker: work speed 30.00,
move speed 2.00, luck 5.00). Records keep the raw integers, so sorting and
export stay exact.
"""

from __future__ import annotations

from enum import IntEnum

from _common.html import e


class WorkerGrade(IntEnum):
    # White in game: Naive workers, and the unused and dev workers below.
    NAIVE = 0
    BASE = 1
    SKILLED = 2
    PROFESSIONAL = 3
    ARTISAN = 4
    NAMED = 5


_BASE_CLASS = 28023
_GRADE_BY_CLASS: dict[int, WorkerGrade] = {
    _BASE_CLASS: WorkerGrade.BASE,
    28024: WorkerGrade.SKILLED,
    28025: WorkerGrade.PROFESSIONAL,
    28026: WorkerGrade.ARTISAN,
    28027: WorkerGrade.NAMED,
}
_NAIVE_WORD = "Naive"
# White in game whatever their class: the dev workers QA Worker: Time / Luck,
# Grand Chamberlain, Temporary Laborer and QA Super Worker (base class), and the
# unused Demibeast Worker 8007 (Skilled class, upgrades into Artisan Fadus 8006).
_WHITE_WORKER_IDS = frozenset({7996, 7997, 7998, 7999, 8000, 8007})

WORK_SPEED_SCALE = 1_000_000
MOVE_SPEED_SCALE = 100
LUCK_SCALE = 10_000

_EMPTY = "-"


def worker_grade(grade_class: int | None, worker_id: int, name: str) -> WorkerGrade | None:
    """The worker's grade, or None for a class this table does not know."""
    if worker_id in _WHITE_WORKER_IDS:
        return WorkerGrade.NAIVE
    grade = _GRADE_BY_CLASS.get(grade_class) if grade_class is not None else None
    if grade is WorkerGrade.BASE and _NAIVE_WORD in name.split():
        return WorkerGrade.NAIVE
    return grade


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
