"""Read queries for the puzzles app."""

from datetime import date, timedelta

from apps.common.time import today_in_romania

from .exceptions import ArchiveUnavailableError, NoPuzzleError
from .models import DailyPuzzle
from .registry import get_games


def get_playable_puzzle(game: str, day: date) -> DailyPuzzle:
    """Return the puzzle a player may play for this game and day.

    Only today's puzzle is playable for now. Future puzzles are reported as missing so their
    existence isn't revealed.
    """
    today = today_in_romania()
    if day > today:
        raise NoPuzzleError()
    if day < today:
        raise ArchiveUnavailableError()
    try:
        return DailyPuzzle.objects.get(game=game, date=day)
    except DailyPuzzle.DoesNotExist:
        raise NoPuzzleError() from None


def get_missing_days(days_ahead: int = 7) -> dict[str, list[date]]:
    """For each registered game, the days from today on that have no puzzle yet."""
    today = today_in_romania()
    upcoming = [today + timedelta(days=offset) for offset in range(days_ahead)]
    scheduled = set(
        DailyPuzzle.objects.filter(date__in=upcoming).values_list("game", "date"),
    )
    missing = {}
    for game in get_games():
        days = [day for day in upcoming if (game.key, day) not in scheduled]
        if days:
            missing[game.key] = days
    return missing
