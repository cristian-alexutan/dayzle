import pytest
from django.core.exceptions import ImproperlyConfigured

from apps.puzzles.models import DailyPuzzle


def test_registered_game_is_listed(clean_registry):
    clean_registry.register_game(key="word", name="Word", content_model=DailyPuzzle)

    assert [game.key for game in clean_registry.get_games()] == ["word"]


def test_unknown_game_key_is_rejected(clean_registry):
    with pytest.raises(ImproperlyConfigured):
        clean_registry.register_game(key="chess", name="Chess", content_model=DailyPuzzle)


def test_game_cannot_be_registered_twice(clean_registry):
    clean_registry.register_game(key="word", name="Word", content_model=DailyPuzzle)

    with pytest.raises(ImproperlyConfigured):
        clean_registry.register_game(key="word", name="Word", content_model=DailyPuzzle)
