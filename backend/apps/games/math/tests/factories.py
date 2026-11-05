import factory

from apps.games.math.models import MathPuzzle
from apps.puzzles.models import Game
from apps.puzzles.tests.factories import DailyPuzzleFactory


class MathPuzzleFactory(factory.django.DjangoModelFactory):
    """Target 253 from 1, 2, 3, 25, 50, 100: (100 × 2) + (50 + 3)."""

    class Meta:
        model = MathPuzzle

    daily_puzzle = factory.SubFactory(DailyPuzzleFactory, game=Game.MATH)
    target = 253
    numbers = factory.LazyFunction(lambda: [1, 2, 3, 25, 50, 100])
    difficulty = "easy"
    min_operations = 3
    solution = factory.LazyFunction(
        lambda: [
            {"left": 100, "op": "*", "right": 2, "result": 200},
            {"left": 50, "op": "+", "right": 3, "result": 53},
            {"left": 200, "op": "+", "right": 53, "result": 253},
        ]
    )
