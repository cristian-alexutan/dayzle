"""Write operations and business rules for the Logic game app.

The player's progress lives in ``GameResult.details``:

- ``suns``: the correct suns on the board, as ``[row, col]`` pairs, in the order placed.
- ``marks``: the X marks, as ``[row, col]`` pairs. They are only notes and are never checked.
- ``moves``: every sun the player placed, in order: ``true`` if correct, ``false`` if a mistake.
  The number of mistakes, the current streak and the score are all computed from it.
"""

import uuid
from dataclasses import dataclass
from datetime import date

from django.db import transaction

from apps.puzzles.models import DailyPuzzle
from apps.results.exceptions import AlreadyPlayedError
from apps.results.models import GameResult
from apps.results.services import complete, save_progress, start_or_resume

from . import rules
from .exceptions import InvalidCellError
from .models import LogicPuzzle
from .selectors import get_playable_logic_puzzle


@dataclass(frozen=True)
class LogicGame:
    """A player's daily game: their result and the day's grid (its solution stays secret)."""

    result: GameResult
    puzzle: LogicPuzzle


@dataclass(frozen=True)
class PlaceOutcome:
    """The game after placing a sun, and what the server said about that sun."""

    game: LogicGame
    correct: bool
    # The suns the new sun broke a rule with, so the frontend can show why it was wrong.
    conflicts: list[rules.Cell]


def open_game(guest_id: uuid.UUID, day: date) -> LogicGame:
    """Return the player's game for the day, starting it (and its clock) on first open."""
    puzzle = get_playable_logic_puzzle(day)
    return LogicGame(start_or_resume(guest_id, puzzle.daily_puzzle), puzzle)


def _cells(details: dict, key: str) -> list[rules.Cell]:
    return [(row, col) for row, col in details.get(key, [])]


def _lock(result: GameResult) -> GameResult:
    """Lock the result so two requests at the same time can't both change it."""
    locked = GameResult.objects.select_for_update().get(pk=result.pk)
    if locked.status == GameResult.Status.COMPLETED:
        raise AlreadyPlayedError()
    return locked


def place_sun(guest_id: uuid.UUID, day: date, row: int, col: int) -> PlaceOutcome:
    """Check one sun against the solution.

    A correct sun stays on the board for good; a wrong one is not kept and counts as a mistake.
    Either way the cell loses its X mark. The last correct sun finishes the game, scored with
    ``rules.score``.
    """
    game = open_game(guest_id, day)
    puzzle = game.puzzle
    cell = (row, col)
    if not rules.is_in_grid(cell, puzzle.size):
        raise InvalidCellError()

    with transaction.atomic():
        result = _lock(game.result)
        suns = _cells(result.details, "suns")
        if cell in suns:
            raise InvalidCellError()

        correct = rules.is_correct(cell, puzzle.solution)
        conflicts = [] if correct else rules.conflicts(cell, suns, puzzle.regions)
        if correct:
            suns.append(cell)
        marks = [mark for mark in _cells(result.details, "marks") if mark != cell]
        moves = [*result.details.get("moves", []), correct]
        details = {
            "suns": [list(sun) for sun in suns],
            "marks": [list(mark) for mark in marks],
            "moves": moves,
        }

        if rules.is_solved(suns, puzzle.solution):
            # ``complete`` measures the duration, and the score needs it, so the score is set
            # right after, in the same transaction: nobody can see the result in between.
            result = complete(result, solved=True, score=0, details=details)
            result.score = rules.score(moves, puzzle.size, result.duration_ms)
            result.save(update_fields=["score", "updated_at"])
        else:
            result = save_progress(result, details)

    return PlaceOutcome(LogicGame(result, puzzle), correct, conflicts)


def save_marks(guest_id: uuid.UUID, day: date, marks: list[rules.Cell]) -> LogicGame:
    """Replace the player's X marks, so a refresh restores them. Marks are never checked.

    Duplicates are dropped, and so are marks on cells that already hold a sun.
    """
    game = open_game(guest_id, day)
    if any(not rules.is_in_grid(mark, game.puzzle.size) for mark in marks):
        raise InvalidCellError()

    with transaction.atomic():
        result = _lock(game.result)
        suns = _cells(result.details, "suns")
        kept = list(dict.fromkeys(mark for mark in marks if mark not in suns))
        details = {**result.details, "marks": [list(mark) for mark in kept]}
        result = save_progress(result, details)
    return LogicGame(result, game.puzzle)


def seed_puzzle(daily_puzzle: DailyPuzzle) -> None:
    """``seed_dev`` hook: give a new day the demo level, until the generator exists."""
    LogicPuzzle.objects.create(
        daily_puzzle=daily_puzzle,
        size=rules.DEMO_SIZE,
        regions=[row[:] for row in rules.DEMO_REGIONS],
        solution=rules.DEMO_SOLUTION[:],
    )
