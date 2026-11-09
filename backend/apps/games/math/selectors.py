"""Read queries for the Math game app."""

from datetime import date

from apps.puzzles.exceptions import NoPuzzleError
from apps.puzzles.models import DailyPuzzle, Game
from apps.puzzles.selectors import get_playable_puzzle
from apps.results.models import GameResult

from .models import MathPuzzle


def get_playable_math_puzzle(day: date) -> MathPuzzle:
    """The day's puzzle, or ``NoPuzzleError`` if the calendar entry has no content yet."""
    puzzle = get_playable_puzzle(Game.MATH, day)
    try:
        return MathPuzzle.objects.select_related("daily_puzzle").get(daily_puzzle=puzzle)
    except MathPuzzle.DoesNotExist:
        raise NoPuzzleError() from None


def has_players(daily_puzzle: DailyPuzzle) -> bool:
    """Whether anyone has opened this day's game, so its saved steps depend on the numbers."""
    return GameResult.objects.filter(daily_puzzle=daily_puzzle).exists()
