"""Database models for the Word game app."""

from django.db import models

from apps.common.models import TimeStampedModel
from apps.puzzles.models import DailyPuzzle, Game


class Word(TimeStampedModel):
    """One entry of the word bank: a valid guess, and possibly an answer."""

    text = models.CharField(max_length=5, unique=True)
    is_answer = models.BooleanField(default=False)

    class Meta:
        ordering = ["text"]

    def __str__(self) -> str:
        return self.text


class WordPuzzle(TimeStampedModel):
    """The content of one daily word: the secret answer of that day's puzzle."""

    daily_puzzle = models.OneToOneField(
        DailyPuzzle,
        on_delete=models.CASCADE,
        related_name="word",
        limit_choices_to={"game": Game.WORD},
    )
    answer = models.ForeignKey(
        Word, on_delete=models.PROTECT, related_name="puzzles", limit_choices_to={"is_answer": True}
    )

    def __str__(self) -> str:
        return str(self.daily_puzzle)
