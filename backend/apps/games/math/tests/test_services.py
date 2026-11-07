import random
import uuid
from datetime import timedelta

import pytest

from apps.common.time import today_in_romania
from apps.games.math import rules, services
from apps.games.math.exceptions import (
    GenerationFailedError,
    InvalidNumbersError,
    InvalidStepError,
    NoStepsError,
)
from apps.games.math.models import MathPuzzle
from apps.games.math.rules import Difficulty, Operator, Step
from apps.puzzles.exceptions import ArchiveUnavailableError, NoPuzzleError
from apps.puzzles.models import Game
from apps.puzzles.tests.factories import DailyPuzzleFactory
from apps.results.exceptions import AlreadyPlayedError
from apps.results.models import GameResult

from .factories import MathPuzzleFactory

pytestmark = pytest.mark.django_db


def steps(*texts: str) -> list[Step]:
    """Steps from text such as "100 * 2"."""
    parsed = (text.split() for text in texts)
    return [Step(int(left), Operator(op), int(right)) for left, op, right in parsed]


SOLVED = ("100 * 2", "50 + 3", "200 + 53")  # today's puzzle: 253 from 1, 2, 3, 25, 50, 100


@pytest.fixture
def today():
    MathPuzzleFactory()
    return today_in_romania()


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


def test_seed_falls_back_to_a_fixed_puzzle_when_generation_fails(monkeypatch):
    def fail(difficulty, rng=None):
        raise GenerationFailedError()

    monkeypatch.setattr(rules, "generate", fail)
    daily_puzzle = DailyPuzzleFactory(game=Game.MATH)

    services.seed_puzzle(daily_puzzle)

    puzzle = MathPuzzle.objects.get(daily_puzzle=daily_puzzle)
    assert (puzzle.target, puzzle.numbers) == (576, [2, 2, 3, 3, 4, 4])
    assert puzzle.solution[-1]["result"] == 576


def test_opening_the_game_starts_it_without_steps(today):
    game = services.open_game(uuid.uuid4(), today)

    assert game.result.status == GameResult.Status.IN_PROGRESS
    assert game.result.details == {}


def test_progress_is_replayed_saved_and_restored(today):
    guest_id = uuid.uuid4()

    services.save_steps(guest_id, today, steps("100 * 2", "50 + 3"))

    saved = services.open_game(guest_id, today).result.details["steps"]
    assert saved == [
        {"left": 100, "op": "*", "right": 2, "result": 200},
        {"left": 50, "op": "+", "right": 3, "result": 53},
    ]


def test_a_reset_saves_an_empty_board(today):
    guest_id = uuid.uuid4()
    services.save_steps(guest_id, today, steps("100 * 2"))

    game = services.save_steps(guest_id, today, [])

    assert game.result.details == {"steps": []}
    assert game.result.status == GameResult.Status.IN_PROGRESS


def test_an_invalid_step_is_rejected_and_keeps_the_saved_board(today):
    guest_id = uuid.uuid4()
    services.save_steps(guest_id, today, steps("100 * 2"))

    with pytest.raises(InvalidStepError) as error:
        services.save_steps(guest_id, today, steps("100 * 2", "200 / 3"))

    assert error.value.details == {"step": 1, "reason": rules.NOT_WHOLE}
    game = services.open_game(guest_id, today)
    assert game.result.status == GameResult.Status.IN_PROGRESS
    assert len(game.result.details["steps"]) == 1


def test_reaching_the_target_scores_1000(today):
    game = services.submit(uuid.uuid4(), today, steps(*SOLVED))

    assert game.result.status == GameResult.Status.COMPLETED
    assert game.result.solved is True
    assert game.result.score == 1000
    assert game.result.duration_ms is not None
    assert game.result.details["final_result"] == 253
    assert game.result.details["operations"] == 3


def test_saving_a_step_that_reaches_the_target_finishes_the_game(today):
    guest_id = uuid.uuid4()
    services.save_steps(guest_id, today, steps(*SOLVED[:2]))

    game = services.save_steps(guest_id, today, steps(*SOLVED))

    assert game.result.status == GameResult.Status.COMPLETED
    assert game.result.solved is True
    assert game.result.score == 1000
    assert game.result.duration_ms is not None
    assert game.result.details == {
        "steps": [
            {"left": 100, "op": "*", "right": 2, "result": 200},
            {"left": 50, "op": "+", "right": 3, "result": 53},
            {"left": 200, "op": "+", "right": 53, "result": 253},
        ],
        "final_result": 253,
        "distance": 0,
        "operations": 3,
    }


def test_saving_steps_that_miss_the_target_keeps_the_game_going(today):
    guest_id = uuid.uuid4()

    game = services.save_steps(guest_id, today, steps("100 * 2", "200 + 50", "3 - 1"))

    assert game.result.status == GameResult.Status.IN_PROGRESS
    assert game.result.completed_at is None
    assert set(game.result.details) == {"steps"}


def test_the_closest_result_is_scored_by_its_distance(today):
    game = services.submit(uuid.uuid4(), today, steps("100 * 2", "200 + 50", "3 - 1"))

    assert game.result.solved is False
    assert game.result.details["final_result"] == 250
    assert game.result.details["distance"] == 3
    assert game.result.score == 840


def test_submitting_without_steps_is_rejected(today):
    guest_id = uuid.uuid4()

    with pytest.raises(NoStepsError):
        services.submit(guest_id, today, [])

    assert services.open_game(guest_id, today).result.status == GameResult.Status.IN_PROGRESS


def test_an_invalid_submit_does_not_end_the_game(today):
    guest_id = uuid.uuid4()

    with pytest.raises(InvalidStepError):
        services.submit(guest_id, today, steps("7 + 1"))

    assert services.open_game(guest_id, today).result.status == GameResult.Status.IN_PROGRESS


@pytest.mark.parametrize("action", [services.save_steps, services.submit])
def test_a_finished_game_cannot_be_played_again(today, action):
    guest_id = uuid.uuid4()
    services.submit(guest_id, today, steps(*SOLVED))

    with pytest.raises(AlreadyPlayedError):
        action(guest_id, today, steps("100 + 1"))


def test_a_day_without_content_has_no_puzzle():
    DailyPuzzleFactory(game=Game.MATH)

    with pytest.raises(NoPuzzleError):
        services.open_game(uuid.uuid4(), today_in_romania())


def test_only_todays_puzzle_is_playable(today):
    with pytest.raises(ArchiveUnavailableError):
        services.open_game(uuid.uuid4(), today - timedelta(days=1))
