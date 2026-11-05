import random
from datetime import timedelta

import pytest

from apps.common.time import today_in_romania
from apps.games.math import rules, services
from apps.games.math.exceptions import InvalidNumbersError
from apps.games.math.models import MathPuzzle
from apps.games.math.rules import Difficulty
from apps.puzzles.models import Game
from apps.puzzles.tests.factories import DailyPuzzleFactory

pytestmark = pytest.mark.django_db


def test_prepare_puzzle_stores_what_the_solver_found():
    content = services.prepare_puzzle([2, 2, 3, 3, 4, 4], 576)

    assert content.target == 576
    assert content.numbers == [2, 2, 3, 3, 4, 4]
    assert content.min_operations == 5
    assert content.difficulty == Difficulty.HARD
    assert len(content.solution) == 5
    assert content.solution[-1]["result"] == 576


@pytest.mark.parametrize(
    ("numbers", "target", "message"),
    [
        ([1, 1, 2, 2, 3, 3], 101, "can't reach the target"),
        ([25, 25, 1, 2, 3, 4], 200, "at most once"),
        ([1, 2, 3, 4, 5, 6], 1000, "between 101 and 999"),
    ],
)
def test_prepare_puzzle_rejects_broken_or_impossible_puzzles(numbers, target, message):
    with pytest.raises(InvalidNumbersError) as error:
        services.prepare_puzzle(numbers, target)
    assert message in error.value.message


def test_a_stored_solution_replays_to_the_target():
    content = services.generate_puzzle(Difficulty.MEDIUM, random.Random(3))
    steps = [
        rules.Step(step["left"], rules.Operator(step["op"]), step["right"])
        for step in content.solution
    ]

    replay = rules.replay(content.numbers, content.target, steps)

    assert replay.solved
    assert content.min_operations == 4


def test_seed_creates_solvable_puzzles_cycling_through_the_difficulties():
    today = today_in_romania()
    days = [DailyPuzzleFactory(game=Game.MATH, date=today + timedelta(days=n)) for n in range(3)]

    for daily_puzzle in days:
        services.seed_puzzle(daily_puzzle)

    puzzles = MathPuzzle.objects.order_by("daily_puzzle__date")
    assert {puzzle.difficulty for puzzle in puzzles} == set(Difficulty)
    for puzzle in puzzles:
        assert services.prepare_puzzle(puzzle.numbers, puzzle.target).min_operations == (
            puzzle.min_operations
        )
