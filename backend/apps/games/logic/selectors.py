"""Read queries for the Logic game app."""

from datetime import date

from apps.puzzles.exceptions import NoPuzzleError
from apps.puzzles.models import Game
from apps.puzzles.selectors import get_playable_puzzle

from .models import LogicPuzzle


def get_playable_logic_puzzle(day: date) -> LogicPuzzle:
    """The day's grid, or ``NoPuzzleError`` if the calendar entry has no grid yet."""
    puzzle = get_playable_puzzle(Game.LOGIC, day)
    try:
        return LogicPuzzle.objects.select_related("daily_puzzle").get(daily_puzzle=puzzle)
    except LogicPuzzle.DoesNotExist:
        raise NoPuzzleError() from None
