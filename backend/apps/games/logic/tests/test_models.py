from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.contrib import admin
from django.core.exceptions import ValidationError

from apps.common.time import today_in_romania
from apps.games.logic import rules, services
from apps.games.logic.admin import LogicPuzzleAdmin
from apps.games.logic.models import LogicPuzzle
from apps.games.logic.selectors import get_playable_logic_puzzle
from apps.puzzles.exceptions import NoPuzzleError
from apps.puzzles.models import Game
from apps.puzzles.registry import get_games
from apps.puzzles.tests.factories import DailyPuzzleFactory
from apps.results.tests.factories import GameResultFactory

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


def transposed_demo_level() -> tuple[list[list[int]], list[int]]:
    """Another valid level: the demo grid mirrored on its diagonal, with its solution."""
    regions = [list(column) for column in zip(*rules.DEMO_REGIONS, strict=True)]
    solution = [0] * rules.DEMO_SIZE
    for row, col in enumerate(rules.DEMO_SOLUTION):
        solution[col] = row
    return regions, solution


def test_an_unplayed_puzzle_can_be_changed():
    puzzle = LogicPuzzleFactory()
    puzzle.regions, puzzle.solution = transposed_demo_level()

    puzzle.full_clean()


def test_a_played_puzzle_cannot_be_changed():
    puzzle = LogicPuzzleFactory()
    GameResultFactory(daily_puzzle=puzzle.daily_puzzle)
    puzzle.regions, puzzle.solution = transposed_demo_level()

    with pytest.raises(ValidationError, match="already started"):
        puzzle.full_clean()


def test_a_played_puzzle_can_still_be_saved_unchanged():
    puzzle = LogicPuzzleFactory()
    GameResultFactory(daily_puzzle=puzzle.daily_puzzle)

    puzzle.full_clean()


def test_the_admin_locks_a_played_puzzle():
    puzzle = LogicPuzzleFactory()
    puzzle_admin = LogicPuzzleAdmin(LogicPuzzle, admin.site)
    # An admin who may do everything, so only the played check can say no.
    request = SimpleNamespace(user=SimpleNamespace(has_perm=lambda perm: True))
    assert puzzle_admin.has_delete_permission(request, puzzle) is True
    assert puzzle_admin.get_readonly_fields(request, puzzle) == ()

    GameResultFactory(daily_puzzle=puzzle.daily_puzzle)

    assert puzzle_admin.has_delete_permission(request, puzzle) is False
    assert set(puzzle_admin.get_readonly_fields(request, puzzle)) == {
        "daily_puzzle",
        "size",
        "regions",
        "solution",
    }


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
