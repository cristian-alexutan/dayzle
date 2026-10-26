import uuid

import factory

from apps.puzzles.tests.factories import DailyPuzzleFactory
from apps.results.models import GameResult


class GameResultFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GameResult

    daily_puzzle = factory.SubFactory(DailyPuzzleFactory)
    guest_id = factory.LazyFunction(uuid.uuid4)
