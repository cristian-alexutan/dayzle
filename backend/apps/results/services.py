"""Write operations and business rules for the results app."""

import uuid
from datetime import date, datetime, timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.common.time import today_in_romania
from apps.puzzles.models import DailyPuzzle
from apps.puzzles.selectors import get_playable_puzzle

from .exceptions import AlreadyPlayedError, NotStartedError
from .models import GameResult
from .selectors import get_result

# Only active time counts towards a result's duration. While a game is visible, the frontend
# sends a heartbeat every 15 seconds; a longer gap between two activities means the player left
# (closed or hid the page), so at most this much of it counts.
ACTIVITY_GAP_CAP = timedelta(seconds=30)


def start_or_resume(guest_id: uuid.UUID, puzzle: DailyPuzzle) -> GameResult:
    """Return the player's result for this puzzle, creating it when they first open it.

    Opening the game starts the clock. A completed result is returned as is; the game decides
    how to show it.
    """
    result, _ = GameResult.objects.get_or_create(
        guest_id=guest_id,
        daily_puzzle=puzzle,
        defaults={"is_archive": puzzle.date < today_in_romania()},
    )
    return result


def _lock_in_progress(result: GameResult) -> GameResult:
    locked = GameResult.objects.select_for_update().get(pk=result.pk)
    if locked.status == GameResult.Status.COMPLETED:
        raise AlreadyPlayedError()
    return locked


def _add_active_time(result: GameResult, now: datetime) -> None:
    gap = min(max(now - result.last_active_at, timedelta(0)), ACTIVITY_GAP_CAP)
    result.active_ms += int(gap.total_seconds() * 1000)
    result.last_active_at = now


@transaction.atomic
def record_activity(result: GameResult) -> GameResult:
    """Count the time since the player's last activity (up to the cap) as active time."""
    locked = _lock_in_progress(result)
    _add_active_time(locked, timezone.now())
    locked.save(update_fields=["active_ms", "last_active_at", "updated_at"])
    return locked


def heartbeat(guest_id: uuid.UUID, game: str, day: date) -> GameResult:
    """Called by the frontend while a game is visible, so thinking time counts as active."""
    puzzle = get_playable_puzzle(game, day)
    result = get_result(guest_id, puzzle)
    if result is None:
        raise NotStartedError()
    return record_activity(result)


@transaction.atomic
def save_progress(result: GameResult, details: dict[str, Any]) -> GameResult:
    """Store the game's in-progress state (e.g. guesses so far) so a refresh can restore it."""
    locked = _lock_in_progress(result)
    _add_active_time(locked, timezone.now())
    locked.details = details
    locked.save(update_fields=["details", "active_ms", "last_active_at", "updated_at"])
    return locked


@transaction.atomic
def complete(
    result: GameResult, *, solved: bool, score: int, details: dict[str, Any] | None = None
) -> GameResult:
    """Finish the game. The duration is the active play time measured on the server."""
    locked = _lock_in_progress(result)
    now = timezone.now()
    _add_active_time(locked, now)
    locked.status = GameResult.Status.COMPLETED
    locked.completed_at = now
    locked.solved = solved
    locked.score = score
    locked.duration_ms = locked.active_ms
    if details is not None:
        locked.details = details
    locked.save()
    return locked
