"""Read queries for the Math game app."""

from apps.puzzles.models import DailyPuzzle
from apps.results.models import GameResult


def has_players(daily_puzzle: DailyPuzzle) -> bool:
    """Whether anyone has opened this day's game, so its saved steps depend on the numbers."""
    return GameResult.objects.filter(daily_puzzle=daily_puzzle).exists()
