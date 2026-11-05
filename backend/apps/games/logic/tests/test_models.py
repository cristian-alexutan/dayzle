from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError

from apps.common.time import today_in_romania
from apps.games.logic import rules, services
from apps.games.logic.models import LogicPuzzle
from apps.games.logic.selectors import get_playable_logic_puzzle
from apps.puzzles.exceptions import NoPuzzleError
from apps.puzzles.models import Game
from apps.puzzles.registry import get_games
from apps.puzzles.tests.factories import DailyPuzzleFactory

from .factories import LogicPuzzleFactory

pytestmark = pytest.mark.django_db


def test_the_demo_level_passes_validation():
    LogicPuzzleFactory.build(daily_puzzle=DailyPuzzleFactory(game=Game.LOGIC)).full_clean()


def test_a_grid_with_several_solutions_is_rejected():
    puzzle = LogicPuzzleFactory.build(
        daily_puzzle=DailyPuzzleFactory(game=Game.LOGIC),
        size=5,
        regions=[[row] * 5 for row in range(5)],
        solution=[0, 2, 4, 1, 3],
    )
    with pytest.raises(ValidationError):
        puzzle.full_clean()


def test_regions_that_are_not_a_list_of_rows_are_rejected():
    puzzle = LogicPuzzleFactory.build(
        daily_puzzle=DailyPuzzleFactory(game=Game.LOGIC), regions="not a grid"
    )
    with pytest.raises(ValidationError):
        puzzle.full_clean()


def test_the_game_is_registered():
    assert "logic" in [game.key for game in get_games()]


def test_seed_gives_a_day_the_demo_level():
    daily_puzzle = DailyPuzzleFactory(game=Game.LOGIC)

    services.seed_puzzle(daily_puzzle)

    puzzle = LogicPuzzle.objects.get(daily_puzzle=daily_puzzle)
    assert puzzle.regions == rules.DEMO_REGIONS
    assert puzzle.solution == rules.DEMO_SOLUTION


def test_todays_puzzle_is_playable():
    puzzle = LogicPuzzleFactory()

    assert get_playable_logic_puzzle(today_in_romania()) == puzzle


def test_a_day_without_a_grid_has_no_puzzle():
    DailyPuzzleFactory(game=Game.LOGIC)

    with pytest.raises(NoPuzzleError):
        get_playable_logic_puzzle(today_in_romania())


def test_a_future_puzzle_is_not_playable():
    tomorrow = today_in_romania() + timedelta(days=1)
    LogicPuzzleFactory(daily_puzzle__date=tomorrow)

    with pytest.raises(NoPuzzleError):
        get_playable_logic_puzzle(tomorrow)
