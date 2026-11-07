"""Read queries for the puzzles app."""

from datetime import date, timedelta

from apps.common.time import today_in_romania

from .exceptions import ArchiveUnavailableError, NoPuzzleError
from .models import DailyPuzzle
from .registry import GameDefinition, get_games


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


def has_content(game: GameDefinition, puzzle: DailyPuzzle) -> bool:
    """Whether the game's content model has an entry for this calendar entry.

    A content model is linked through a ``daily_puzzle`` field (see CONTRIBUTING); one without
    it counts as always having content.
    """
    model = game.content_model
    if not any(field.name == "daily_puzzle" for field in model._meta.get_fields()):
        return True
    return model.objects.filter(daily_puzzle=puzzle).exists()


def get_missing_days(days_ahead: int = 7) -> dict[str, list[date]]:
    """For each game scheduled by admins, the days from today on that have no puzzle yet."""
    today = today_in_romania()
    upcoming = [today + timedelta(days=offset) for offset in range(days_ahead)]
    scheduled = set(
        DailyPuzzle.objects.filter(date__in=upcoming).values_list("game", "date"),
    )
    missing = {}
    for game in get_games():
        if not game.scheduled_by_admin:
            continue
        days = [day for day in upcoming if (game.key, day) not in scheduled]
        if days:
            missing[game.key] = days
    return missing
