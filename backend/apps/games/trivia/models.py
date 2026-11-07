"""Database models for the Trivia game app."""

from django.db import models

from apps.common.models import TimeStampedModel
from apps.puzzles.models import DailyPuzzle, Game


class Category(models.TextChoices):
    HISTORY = "history", "History"
    GEOGRAPHY = "geography", "Geography"
    SCIENCE = "science", "Science"
    CULTURE = "culture", "Culture"
    SPORTS = "sports", "Sports"
    GENERAL = "general", "General knowledge"


class Difficulty(models.TextChoices):
    EASY = "easy", "Easy"
    MEDIUM = "medium", "Medium"
    HARD = "hard", "Hard"


class Question(TimeStampedModel):
    """One entry of the question bank, in Romanian. It can be used on several days."""

    text = models.CharField(max_length=300, unique=True)
    category = models.CharField(max_length=16, choices=Category.choices)
    difficulty = models.CharField(max_length=8, choices=Difficulty.choices)

    class Meta:
        ordering = ["category", "text"]

    def __str__(self) -> str:
        return self.text


class Choice(models.Model):
    """One answer option of a question. Each question has 4 choices, exactly one correct."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=150)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["question"],
                condition=models.Q(is_correct=True),
                name="one_correct_choice_per_question",
            ),
        ]

    def __str__(self) -> str:
        return self.text


class TriviaPuzzle(TimeStampedModel):
    """The content of one daily quiz: its 5 questions, in order (see ``TriviaPuzzleQuestion``)."""

    daily_puzzle = models.OneToOneField(
        DailyPuzzle,
        on_delete=models.CASCADE,
        related_name="trivia",
        limit_choices_to={"game": Game.TRIVIA},
    )
    questions = models.ManyToManyField(
        Question, through="TriviaPuzzleQuestion", related_name="puzzles"
    )

    def __str__(self) -> str:
        return str(self.daily_puzzle)


class TriviaPuzzleQuestion(models.Model):
    """One question of a daily quiz and its position (1 to 5)."""

    puzzle = models.ForeignKey(TriviaPuzzle, on_delete=models.CASCADE, related_name="entries")
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="entries")
    position = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["puzzle", "position"], name="one_question_per_position"
            ),
            models.UniqueConstraint(fields=["puzzle", "question"], name="no_repeated_question"),
        ]

    def __str__(self) -> str:
        return f"{self.position}. {self.question}"
