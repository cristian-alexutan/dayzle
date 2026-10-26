from datetime import timedelta

import pytest

from apps.common.time import today_in_romania
from apps.puzzles.exceptions import ArchiveUnavailableError, NoPuzzleError
from apps.puzzles.models import Game
from apps.puzzles.selectors import get_missing_days, get_playable_puzzle

from .factories import DailyPuzzleFactory

pytestmark = pytest.mark.django_db


def test_todays_puzzle_is_playable():
    puzzle = DailyPuzzleFactory(game=Game.WORD)

    assert get_playable_puzzle(Game.WORD, today_in_romania()) == puzzle


def test_missing_puzzle_raises_no_puzzle():
    DailyPuzzleFactory(game=Game.MATH)

    with pytest.raises(NoPuzzleError):
        get_playable_puzzle(Game.WORD, today_in_romania())


def test_past_puzzle_is_not_playable_yet():
    yesterday = today_in_romania() - timedelta(days=1)
    DailyPuzzleFactory(date=yesterday)

    with pytest.raises(ArchiveUnavailableError):
        get_playable_puzzle(Game.WORD, yesterday)


def test_future_puzzle_is_reported_as_missing():
    tomorrow = today_in_romania() + timedelta(days=1)
    DailyPuzzleFactory(date=tomorrow)

    with pytest.raises(NoPuzzleError):
        get_playable_puzzle(Game.WORD, tomorrow)


def test_missing_days_lists_unscheduled_days_for_registered_games(clean_registry):
    clean_registry.register_game(key="word", name="Word", content_model=object)
    today = today_in_romania()
    DailyPuzzleFactory(date=today)

    missing = get_missing_days(days_ahead=3)

    assert missing == {"word": [today + timedelta(days=1), today + timedelta(days=2)]}
