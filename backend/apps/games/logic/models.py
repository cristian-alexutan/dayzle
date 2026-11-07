"""Database models for the Logic game app."""

from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimeStampedModel
from apps.puzzles.models import DailyPuzzle, Game
from apps.results.models import GameResult

from . import rules


def _is_int_list(value) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, int) and not isinstance(item, bool) for item in value
    )


class LogicPuzzle(TimeStampedModel):
    """The content of one daily logic puzzle: the colored grid and its secret solution."""

    daily_puzzle = models.OneToOneField(
        DailyPuzzle,
        on_delete=models.CASCADE,
        related_name="logic",
        limit_choices_to={"game": Game.LOGIC},
    )
    size = models.PositiveSmallIntegerField(default=rules.DEMO_SIZE)
    regions = models.JSONField(
        help_text="One list per row with the region number (0 to size - 1) of every cell.",
    )
    # Secret until the game is finished: never sent to the player while they can still play.
    solution = models.JSONField(
        help_text="The column (0 to size - 1) of the sun on every row, e.g. [2, 0, 4, 1, 3, 5].",
    )

    def __str__(self) -> str:
        return str(self.daily_puzzle)

    def has_been_played(self) -> bool:
        """Whether a player has opened this puzzle. Its content must not change after that:
        their suns were checked against this solution."""
        if self.pk is None:
            return False
        saved_day = LogicPuzzle.objects.filter(pk=self.pk).values_list("daily_puzzle", flat=True)
        return GameResult.objects.filter(daily_puzzle__in=saved_day).exists()

    def _content_changed(self) -> bool:
        saved = (
            LogicPuzzle.objects.filter(pk=self.pk)
            .values("daily_puzzle", "size", "regions", "solution")
            .first()
        )
        current = {
            "daily_puzzle": self.daily_puzzle_id,
            "size": self.size,
            "regions": self.regions,
            "solution": self.solution,
        }
        return saved != current

    def clean(self) -> None:
        """Reject grids that break the rules or don't have exactly one solution, and any change
        once players have started the puzzle."""
        if self.has_been_played() and self._content_changed():
            raise ValidationError(
                "Players have already started this puzzle, so it can't be changed anymore."
            )
        if not (isinstance(self.regions, list) and all(_is_int_list(row) for row in self.regions)):
            raise ValidationError({"regions": "Enter a list of rows, each a list of numbers."})
        if not _is_int_list(self.solution):
            raise ValidationError({"solution": "Enter a list of numbers, one for each row."})
        problems = rules.validate_puzzle(self.size, self.regions, self.solution)
        if problems:
            raise ValidationError(problems)
