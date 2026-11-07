import random

import pytest

from apps.games.math import rules
from apps.games.math.exceptions import (
    GenerationFailedError,
    InvalidNumbersError,
    InvalidStepError,
)
from apps.games.math.rules import Difficulty, Operator, Step


def step(text: str) -> Step:
    """Build a step from text such as "25 * 8"."""
    left, op, right = text.split()
    return Step(int(left), Operator(op), int(right))


def steps(*texts: str) -> list[Step]:
    return [step(text) for text in texts]


@pytest.mark.parametrize(
    "numbers",
    [
        (1, 2, 3, 4, 5, 6),  # no large numbers
        (25, 50, 75, 100, 1, 1),  # all four large numbers, a small number twice
        (10, 10, 9, 9, 100, 25),
    ],
)
def test_validate_numbers_accepts_valid_sets(numbers):
    rules.validate_numbers(numbers)


@pytest.mark.parametrize(
    "numbers",
    [
        (1, 2, 3, 4, 5),  # too few
        (1, 2, 3, 4, 5, 6, 7),  # too many
        (3, 3, 3, 4, 5, 6),  # a small number three times
        (25, 25, 1, 2, 3, 4),  # a large number twice
        (0, 1, 2, 3, 4, 5),
        (11, 1, 2, 3, 4, 5),
        (30, 1, 2, 3, 4, 5),
        (-1, 1, 2, 3, 4, 5),
    ],
)
def test_validate_numbers_rejects_invalid_sets(numbers):
    with pytest.raises(InvalidNumbersError):
        rules.validate_numbers(numbers)


@pytest.mark.parametrize(
    ("target", "valid"), [(100, False), (101, True), (999, True), (1000, False)]
)
def test_validate_target(target, valid):
    if valid:
        rules.validate_target(target)
    else:
        with pytest.raises(InvalidNumbersError):
            rules.validate_target(target)


@pytest.mark.parametrize(
    ("text", "expected"),
    [("25 + 8", 33), ("25 * 8", 200), ("25 - 8", 17), ("100 / 4", 25), ("7 / 7", 1)],
)
def test_apply(text, expected):
    s = step(text)
    assert rules.apply(s.left, s.op, s.right) == expected


@pytest.mark.parametrize(
    ("text", "reason"),
    [("5 - 5", rules.NOT_POSITIVE), ("3 - 8", rules.NOT_POSITIVE), ("7 / 2", rules.NOT_WHOLE)],
)
def test_apply_rejects_results_that_are_not_positive_whole_numbers(text, reason):
    s = step(text)
    with pytest.raises(InvalidStepError) as error:
        rules.apply(s.left, s.op, s.right)
    assert error.value.reason == reason


NUMBERS = (1, 2, 3, 25, 50, 100)


def test_replay_solves_the_puzzle():
    replay = rules.replay(NUMBERS, 253, steps("100 * 2", "50 + 3", "200 + 53"))
    assert [played.result for played in replay.steps] == [200, 53, 253]
    assert replay.board == (1, 25, 253)
    assert replay.produced == (253,)
    assert replay.final_result == 253
    assert replay.distance == 0
    assert replay.solved is True


def test_replay_without_steps_has_no_result():
    replay = rules.replay(NUMBERS, 253, [])
    assert replay.board == NUMBERS
    assert replay.final_result is None
    assert replay.distance is None
    assert replay.solved is False


def test_a_starting_number_never_counts_as_the_result():
    replay = rules.replay(NUMBERS, 101, steps("2 + 3"))
    assert replay.final_result == 5
    assert replay.distance == 96


def test_the_closest_computed_number_counts_even_if_it_is_not_the_last():
    replay = rules.replay(NUMBERS, 152, steps("100 + 50", "3 - 2"))
    assert replay.produced == (1, 150)
    assert replay.final_result == 150
    assert replay.distance == 2
    assert replay.solved is False


def test_computed_numbers_can_be_used_in_later_steps():
    replay = rules.replay(NUMBERS, 999, steps("2 + 1", "100 * 3", "300 / 3"))
    assert replay.steps[-1].result == 100
    assert replay.final_result == 100


def test_equal_starting_numbers_can_both_be_used():
    replay = rules.replay((5, 5, 1, 2, 3, 4), 101, steps("5 * 5", "25 * 4"))
    assert replay.final_result == 100


def test_the_starting_copy_of_a_value_is_used_up_first():
    # 25 * 4 makes a second 100; "100 - 3" uses the starting 100, so the computed one stays.
    replay = rules.replay((1, 3, 4, 25, 50, 100), 101, steps("25 * 4", "100 - 3"))
    assert replay.produced == (97, 100)
    assert replay.final_result == 100
    assert replay.distance == 1


@pytest.mark.parametrize(
    ("played", "index", "reason"),
    [
        (["7 + 1"], 0, rules.UNAVAILABLE_NUMBER),  # not on the board
        (["100 + 1", "100 + 2"], 1, rules.UNAVAILABLE_NUMBER),  # 100 already used
        (["2 + 2"], 0, rules.UNAVAILABLE_NUMBER),  # only one 2
        (["2 + 3", "5 + 5"], 1, rules.UNAVAILABLE_NUMBER),  # only one 5
        (["50 + 1", "25 / 2"], 1, rules.NOT_WHOLE),
        (["50 - 50"], 0, rules.UNAVAILABLE_NUMBER),
        (["25 - 50"], 0, rules.NOT_POSITIVE),
        (["3 - 3"], 0, rules.UNAVAILABLE_NUMBER),
        (["2 + 1", "3 - 3"], 1, rules.NOT_POSITIVE),  # a computed 3 and the starting 3
    ],
)
def test_replay_rejects_invalid_steps(played, index, reason):
    with pytest.raises(InvalidStepError) as error:
        rules.replay(NUMBERS, 999, steps(*played))
    assert (error.value.index, error.value.reason) == (index, reason)


def test_no_step_may_follow_the_target():
    with pytest.raises(InvalidStepError) as error:
        rules.replay(NUMBERS, 101, steps("100 + 1", "2 + 3"))
    assert (error.value.index, error.value.reason) == (1, rules.TARGET_REACHED)


def test_at_most_five_steps():
    five = ["1 + 1", "2 + 2", "3 + 3", "4 * 6", "24 * 2"]
    assert rules.replay((1, 1, 2, 2, 3, 3), 999, steps(*five)).final_result == 48
    with pytest.raises(InvalidStepError) as error:
        rules.replay((1, 1, 2, 2, 3, 3), 999, steps(*five, "48 + 48"))
    assert (error.value.index, error.value.reason) == (5, rules.TOO_MANY_STEPS)


@pytest.mark.parametrize(
    ("candidates", "target", "expected"),
    [([150, 1], 152, 150), ([499, 501], 500, 499), ([501, 499], 500, 499), ([], 500, None)],
)
def test_closest(candidates, target, expected):
    assert rules.closest(candidates, target) == expected


@pytest.mark.parametrize(
    ("distance", "expected"),
    [(0, 1000), (1, 880), (5, 800), (20, 500), (44, 20), (45, 0), (300, 0)],
)
def test_score(distance, expected):
    assert rules.score(distance) == expected


@pytest.mark.parametrize(
    ("operations", "expected"),
    [(1, Difficulty.EASY), (3, Difficulty.EASY), (4, Difficulty.MEDIUM), (5, Difficulty.HARD)],
)
def test_difficulty_for(operations, expected):
    assert rules.difficulty_for(operations) == expected


@pytest.mark.parametrize("operations", [0, 6])
def test_difficulty_for_rejects_impossible_counts(operations):
    with pytest.raises(ValueError):
        rules.difficulty_for(operations)


def assert_replays_to_target(numbers, target, solution):
    """The solver's steps must follow the same rules as a player's."""
    replay = rules.replay(numbers, target, [played.step for played in solution.steps])
    assert replay.solved
    assert len(replay.steps) == solution.operations


@pytest.mark.parametrize(
    ("numbers", "target", "operations"),
    [
        ((1, 2, 3, 4, 5, 100), 101, 1),  # 100 + 1
        # 25 * 4 * 2: no pair reaches 200 (at most 25 * 5 = 125).
        ((1, 1, 2, 4, 5, 25), 200, 2),
        # For numbers of at least 2 the product is the largest result, and no 4 of these
        # numbers multiply to 720 (at most 3 * 4 * 5 * 6 = 360), so it needs 2 * 3 * 4 * 5 * 6.
        ((1, 2, 3, 4, 5, 6), 720, 4),
        # 576 is the product of all six numbers, and five of them give at most 288.
        ((2, 2, 3, 3, 4, 4), 576, 5),
    ],
)
def test_solve_finds_a_shortest_solution(numbers, target, operations):
    solution = rules.solve(numbers, target)
    assert solution is not None
    assert solution.operations == operations
    assert_replays_to_target(numbers, target, solution)


@pytest.mark.parametrize(
    ("numbers", "target"),
    [
        ((1, 1, 2, 2, 3, 3), 101),  # the most they can make is (1 + 2) * (1 + 2) * 3 * 3 = 81
        ((1, 2, 3, 4, 5, 6), 997),  # a large prime these small numbers miss
    ],
)
def test_solve_returns_none_for_impossible_puzzles(numbers, target):
    assert rules.solve(numbers, target) is None


def test_reachable_agrees_with_solve():
    numbers = (2, 5, 7, 9, 10, 100)
    solutions = rules.reachable(numbers)
    assert all(rules.TARGET_MIN <= target <= rules.TARGET_MAX for target in solutions)
    for target in (101, 250, 503, 777, 998):
        assert solutions[target].operations == rules.solve(numbers, target).operations
        assert_replays_to_target(numbers, target, solutions[target])


def test_reachable_is_empty_when_nothing_can_be_reached():
    assert rules.reachable((1, 1, 2, 2, 3, 3)) == {}


def test_random_numbers_follow_the_rules():
    rng = random.Random(0)
    for _ in range(200):
        numbers = rules.random_numbers(rng)
        rules.validate_numbers(numbers)
        assert numbers == tuple(sorted(numbers))


@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_generate_matches_the_difficulty(difficulty):
    puzzle = rules.generate(difficulty, random.Random(7))
    rules.validate_numbers(puzzle.numbers)
    rules.validate_target(puzzle.target)
    assert puzzle.difficulty == difficulty
    assert rules.difficulty_for(puzzle.solution.operations) == difficulty
    assert rules.solve(puzzle.numbers, puzzle.target).operations == puzzle.solution.operations
    assert_replays_to_target(puzzle.numbers, puzzle.target, puzzle.solution)


def test_generate_is_repeatable_with_a_seed():
    first = rules.generate(Difficulty.MEDIUM, random.Random(42))
    second = rules.generate(Difficulty.MEDIUM, random.Random(42))
    assert first == second


def test_generate_gives_up_after_the_attempts():
    class OnlyTinyNumbers(random.Random):
        def randint(self, a, b):
            return 0

        def sample(self, population, k):
            return [1, 1, 2, 2, 3, 3][:k]

    with pytest.raises(GenerationFailedError):
        rules.generate(Difficulty.EASY, OnlyTinyNumbers(), attempts=3)
