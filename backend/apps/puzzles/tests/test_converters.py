from datetime import date

import pytest

from apps.common.time import today_in_romania
from apps.puzzles.converters import GameDayConverter


def test_today_resolves_to_the_romanian_game_day():
    assert GameDayConverter().to_python("today") == today_in_romania()


def test_iso_date_is_parsed():
    assert GameDayConverter().to_python("2026-10-26") == date(2026, 10, 26)


def test_impossible_date_does_not_match():
    with pytest.raises(ValueError):
        GameDayConverter().to_python("2026-13-45")
