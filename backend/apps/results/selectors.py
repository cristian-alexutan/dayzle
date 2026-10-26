"""Read queries for the results app."""

import uuid

from apps.puzzles.models import DailyPuzzle

from .models import GameResult


def get_result(guest_id: uuid.UUID, puzzle: DailyPuzzle) -> GameResult | None:
    return GameResult.objects.filter(guest_id=guest_id, daily_puzzle=puzzle).first()
