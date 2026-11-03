import factory

from apps.games.word.models import Word, WordPuzzle
from apps.puzzles.models import Game
from apps.puzzles.tests.factories import DailyPuzzleFactory


class WordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Word
        django_get_or_create = ["text"]

    text = "carte"
    is_answer = True


class WordPuzzleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WordPuzzle

    daily_puzzle = factory.SubFactory(DailyPuzzleFactory, game=Game.WORD)
    answer = factory.SubFactory(WordFactory)
