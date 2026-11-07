import factory

from apps.games.logic import rules
from apps.games.logic.models import LogicPuzzle
from apps.puzzles.models import Game
from apps.puzzles.tests.factories import DailyPuzzleFactory


class LogicPuzzleFactory(factory.django.DjangoModelFactory):
    """Today's logic puzzle with the demo level."""

    class Meta:
        model = LogicPuzzle

    daily_puzzle = factory.SubFactory(DailyPuzzleFactory, game=Game.LOGIC)
    size = rules.DEMO_SIZE
    regions = factory.LazyFunction(lambda: [row[:] for row in rules.DEMO_REGIONS])
    solution = factory.LazyFunction(lambda: rules.DEMO_SOLUTION[:])
