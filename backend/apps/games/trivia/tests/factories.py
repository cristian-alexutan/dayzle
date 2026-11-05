import factory

from apps.games.trivia.models import (
    Category,
    Choice,
    Difficulty,
    Question,
    TriviaPuzzle,
    TriviaPuzzleQuestion,
)
from apps.puzzles.models import Game
from apps.puzzles.tests.factories import DailyPuzzleFactory


class QuestionFactory(factory.django.DjangoModelFactory):
    """A question with 4 choices; the first one ("A") is correct."""

    class Meta:
        model = Question
        skip_postgeneration_save = True

    text = factory.Sequence(lambda n: f"Întrebarea {n}?")
    category = Category.GENERAL
    difficulty = Difficulty.EASY

    @factory.post_generation
    def choices(self, create, extracted, **kwargs):
        texts = extracted or ["A", "B", "C", "D"]
        Choice.objects.bulk_create(
            Choice(question=self, text=text, is_correct=index == 0)
            for index, text in enumerate(texts)
        )


class TriviaPuzzleFactory(factory.django.DjangoModelFactory):
    """Today's quiz with 5 questions, one per category (pass ``questions`` to choose them)."""

    class Meta:
        model = TriviaPuzzle
        skip_postgeneration_save = True

    daily_puzzle = factory.SubFactory(DailyPuzzleFactory, game=Game.TRIVIA)

    @factory.post_generation
    def questions(self, create, extracted, **kwargs):
        questions = extracted or [
            QuestionFactory(category=category) for category in list(Category)[:5]
        ]
        for position, question in enumerate(questions, start=1):
            TriviaPuzzleQuestion.objects.create(puzzle=self, question=question, position=position)
