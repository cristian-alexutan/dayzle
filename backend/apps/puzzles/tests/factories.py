import factory

from apps.common.time import today_in_romania
from apps.puzzles.models import DailyPuzzle, Game


class DailyPuzzleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DailyPuzzle

    game = Game.WORD
    date = factory.LazyFunction(today_in_romania)
