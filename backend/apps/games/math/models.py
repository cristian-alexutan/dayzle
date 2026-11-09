"""Database models for the Math game app."""

from django.db import models

from apps.common.models import TimeStampedModel
from apps.puzzles.models import DailyPuzzle, Game

from .rules import Difficulty

DIFFICULTY_CHOICES = [(difficulty.value, difficulty.name.capitalize()) for difficulty in Difficulty]


class MathPuzzle(TimeStampedModel):
    """The content of one daily Math puzzle: the target and the 6 starting numbers.

    ``difficulty``, ``min_operations`` and ``solution`` come from the solver when the puzzle is
    saved. They are secret until the player finishes, since they hint at the answer.
    """

    daily_puzzle = models.OneToOneField(
        DailyPuzzle,
        on_delete=models.CASCADE,
        related_name="math",
        limit_choices_to={"game": Game.MATH},
    )
    target = models.PositiveSmallIntegerField()
    # The 6 starting numbers, in the order players see them.
    numbers = models.JSONField()
    difficulty = models.CharField(max_length=8, choices=DIFFICULTY_CHOICES)
    min_operations = models.PositiveSmallIntegerField()
    # Steps as {"left", "op", "right", "result"}, the same format as a player's steps.
    solution = models.JSONField(default=list)

    def __str__(self) -> str:
        return str(self.daily_puzzle)
