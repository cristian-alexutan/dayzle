"""Write operations and business rules for the Logic game app.

The player's progress lives in ``GameResult.details``:

- ``suns``: the suns on the board, as ``[row, col]`` pairs. Only suns that break no rule are kept.
- ``marks``: the X marks, as ``[row, col]`` pairs. They are the player's notes and are never
  checked.
- ``mistakes``: how many suns were rejected for breaking a rule.

Nothing is checked against the solution while playing, so the game never tells the player where
a sun belongs. Every puzzle has exactly one solution, so a full board with no rule broken is that
solution and finishes the game.
"""

import uuid
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from django.db import transaction

from apps.puzzles.models import DailyPuzzle
from apps.results.exceptions import AlreadyPlayedError
from apps.results.models import GameResult
from apps.results.services import complete, save_progress, start_or_resume

from . import rules
from .exceptions import InvalidCellError
from .models import LogicPuzzle
from .selectors import get_playable_logic_puzzle


class CellContent(StrEnum):
    EMPTY = "empty"
    MARK = "mark"
    SUN = "sun"


@dataclass(frozen=True)
class LogicGame:
    """A player's daily game: their result and the day's grid (its solution stays secret)."""

    result: GameResult
    puzzle: LogicPuzzle


@dataclass(frozen=True)
class CellOutcome:
    """The game after changing a cell, and whether a new sun was rejected."""

    game: LogicGame
    rejected: bool
    # The suns a rejected sun broke a rule with, so the frontend can show why.
    conflicts: list[rules.Cell]


def open_game(guest_id: uuid.UUID, day: date) -> LogicGame:
    """Return the player's game for the day, starting it (and its clock) on first open."""
    puzzle = get_playable_logic_puzzle(day)
    return LogicGame(start_or_resume(guest_id, puzzle.daily_puzzle), puzzle)


def _cells(details: dict, key: str) -> list[rules.Cell]:
    return [(row, col) for row, col in details.get(key, [])]


def _details(suns: list[rules.Cell], marks: list[rules.Cell], mistakes: int) -> dict:
    return {
        "suns": [list(sun) for sun in suns],
        "marks": [list(mark) for mark in marks],
        "mistakes": mistakes,
    }


def _lock(result: GameResult) -> GameResult:
    """Lock the result so two requests at the same time can't both change it."""
    locked = GameResult.objects.select_for_update().get(pk=result.pk)
    if locked.status == GameResult.Status.COMPLETED:
        raise AlreadyPlayedError()
    return locked


def set_cell(
    guest_id: uuid.UUID, day: date, row: int, col: int, content: CellContent
) -> CellOutcome:
    """Make a cell empty, put an X on it, or place a sun.

    A new sun that breaks a rule with a sun already on the board is rejected: it isn't kept,
    the cell stays as it was, and it counts as a mistake. A sun that breaks no rule replaces the
    cell's X. Placing the last sun finishes the game, scored with ``rules.score``.
    """
    game = open_game(guest_id, day)
    puzzle = game.puzzle
    cell = (row, col)
    if not rules.is_in_grid(cell, puzzle.size):
        raise InvalidCellError()

    with transaction.atomic():
        result = _lock(game.result)
        suns = _cells(result.details, "suns")
        marks = _cells(result.details, "marks")
        mistakes = result.details.get("mistakes", 0)
        others = [sun for sun in suns if sun != cell]
        conflicts: list[rules.Cell] = []

        if content == CellContent.SUN and cell not in suns:
            conflicts = rules.conflicts(cell, suns, puzzle.regions)
            if conflicts:
                mistakes += 1
            else:
                suns = [*suns, cell]
                marks = [mark for mark in marks if mark != cell]
        elif content == CellContent.MARK:
            suns = others
            if cell not in marks:
                marks = [*marks, cell]
        elif content == CellContent.EMPTY:
            suns = others
            marks = [mark for mark in marks if mark != cell]

        details = _details(suns, marks, mistakes)
        if rules.is_full(suns, puzzle.size):
            # ``complete`` measures the duration, and the score needs it, so the score is set
            # right after, in the same transaction: nobody can see the result in between.
            result = complete(result, solved=True, score=0, details=details)
            result.score = rules.score(puzzle.size, result.duration_ms, mistakes)
            result.save(update_fields=["score", "updated_at"])
        else:
            result = save_progress(result, details)

    return CellOutcome(LogicGame(result, puzzle), rejected=bool(conflicts), conflicts=conflicts)


def clear_board(guest_id: uuid.UUID, day: date) -> LogicGame:
    """Remove every sun and X, to start the grid again. Mistakes and time are kept."""
    game = open_game(guest_id, day)
    with transaction.atomic():
        result = _lock(game.result)
        mistakes = result.details.get("mistakes", 0)
        result = save_progress(result, _details([], [], mistakes))
    return LogicGame(result, game.puzzle)


def seed_puzzle(daily_puzzle: DailyPuzzle) -> None:
    """``seed_dev`` hook: give a new day the demo level, until the generator exists."""
    LogicPuzzle.objects.create(
        daily_puzzle=daily_puzzle,
        size=rules.DEMO_SIZE,
        regions=[row[:] for row in rules.DEMO_REGIONS],
        solution=rules.DEMO_SOLUTION[:],
    )
