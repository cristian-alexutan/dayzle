"""Write operations and business rules for the results app."""

import uuid
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.common.time import today_in_romania
from apps.puzzles.models import DailyPuzzle

from .exceptions import AlreadyPlayedError
from .models import GameResult


def start_or_resume(guest_id: uuid.UUID, puzzle: DailyPuzzle) -> GameResult:
    """Return the player's result for this puzzle, creating it when they first open it.

    A completed result is returned as is; the game decides how to show it.
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


@transaction.atomic
def save_progress(result: GameResult, details: dict[str, Any]) -> GameResult:
    """Store the game's in-progress state (e.g. guesses so far) so a refresh can restore it."""
    locked = _lock_in_progress(result)
    locked.details = details
    locked.save(update_fields=["details", "updated_at"])
    return locked


@transaction.atomic
def complete(
    result: GameResult, *, solved: bool, score: int, details: dict[str, Any] | None = None
) -> GameResult:
    """Finish the game. The duration is measured on the server from ``started_at``."""
    locked = _lock_in_progress(result)
    now = timezone.now()
    locked.status = GameResult.Status.COMPLETED
    locked.completed_at = now
    locked.solved = solved
    locked.score = score
    locked.duration_ms = int((now - locked.started_at).total_seconds() * 1000)
    if details is not None:
        locked.details = details
    locked.save()
    return locked
