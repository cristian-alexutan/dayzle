"""Database models for the puzzles app."""

from django.db import models

from apps.common.models import TimeStampedModel


class Game(models.TextChoices):
    WORD = "word", "Word"
    LOGIC = "logic", "Logic"
    MATH = "math", "Math"
    TRIVIA = "trivia", "Trivia"
    GEO = "geo", "GeoGuesser"


class DailyPuzzle(TimeStampedModel):
    """Calendar entry: game X has a puzzle on day Y. Content lives in each game's own model."""

    game = models.CharField(max_length=16, choices=Game.choices)
    date = models.DateField()

    class Meta:
        ordering = ["-date", "game"]
        constraints = [
            models.UniqueConstraint(fields=["game", "date"], name="one_puzzle_per_game_per_day"),
        ]

    def __str__(self) -> str:
        return f"{self.get_game_display()} {self.date.isoformat()}"
