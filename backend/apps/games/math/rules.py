"""Rules of the Math game that need no database: validation, step replay, scoring and solver.

Broken rules raise the app's domain errors, so the API reports them in the shared error format.
"""

import random
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from .exceptions import GenerationFailedError, InvalidNumbersError, InvalidStepError

NUMBER_COUNT = 6
MAX_STEPS = NUMBER_COUNT - 1
TARGET_MIN = 101
TARGET_MAX = 999
SMALL_NUMBERS = range(1, 11)
MAX_SMALL_COPIES = 2
LARGE_NUMBERS = (25, 50, 75, 100)
EXACT_SCORE = 1000


class Operator(StrEnum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# Why a step was rejected; the API passes these on in the error details.
UNAVAILABLE_NUMBER = "unavailable_number"
NOT_POSITIVE = "not_positive"
NOT_WHOLE = "not_whole"
TOO_MANY_STEPS = "too_many_steps"
TARGET_REACHED = "target_reached"


@dataclass(frozen=True)
class Step:
    """One move as the player sends it: two numbers from the board and an operator."""

    left: int
    op: Operator
    right: int


@dataclass(frozen=True)
class PlayedStep:
    step: Step
    result: int


@dataclass(frozen=True)
class Replay:
    """The board after replaying a player's steps from the starting numbers."""

    steps: tuple[PlayedStep, ...]
    board: tuple[int, ...]
    produced: tuple[int, ...]
    final_result: int | None
    distance: int | None
    solved: bool


@dataclass(frozen=True)
class Solution:
    steps: tuple[PlayedStep, ...]

    @property
    def operations(self) -> int:
        return len(self.steps)


@dataclass(frozen=True)
class GeneratedPuzzle:
    numbers: tuple[int, ...]
    target: int
    solution: Solution
    difficulty: Difficulty


def validate_numbers(numbers: Sequence[int]) -> None:
    """Check a starting set: 6 numbers, 1 to 10 at most twice each, 25/50/75/100 at most once."""
    if len(numbers) != NUMBER_COUNT:
        raise InvalidNumbersError(f"A puzzle needs exactly {NUMBER_COUNT} numbers.")
    for number, count in sorted(Counter(numbers).items()):
        if number in LARGE_NUMBERS:
            if count > 1:
                raise InvalidNumbersError(f"{number} can appear at most once.")
        elif number in SMALL_NUMBERS:
            if count > MAX_SMALL_COPIES:
                raise InvalidNumbersError(f"{number} can appear at most twice.")
        else:
            raise InvalidNumbersError(f"{number} is not allowed: use 1 to 10, 25, 50, 75 or 100.")


def validate_target(target: int) -> None:
    if not TARGET_MIN <= target <= TARGET_MAX:
        raise InvalidNumbersError(f"The target must be between {TARGET_MIN} and {TARGET_MAX}.")


def apply(left: int, op: Operator, right: int) -> int:
    """Compute one step. The result must be a positive whole number."""
    if op == Operator.ADD:
        return left + right
    if op == Operator.MUL:
        return left * right
    if op == Operator.SUB:
        if left <= right:
            raise InvalidStepError(NOT_POSITIVE)
        return left - right
    if left % right != 0:
        raise InvalidStepError(NOT_WHOLE)
    return left // right


def closest(candidates: Iterable[int], target: int) -> int | None:
    """The candidate nearest to the target; on a tie, the smaller one."""
    return min(candidates, key=lambda number: (abs(number - target), number), default=None)


def replay(numbers: Sequence[int], target: int, steps: Sequence[Step]) -> Replay:
    """Replay the player's steps from the starting numbers, ignoring anything computed elsewhere.

    The board is a multiset: a step names values, not tiles. When a value is both a starting
    number and a computed one, the starting copy is used up first, which keeps computed numbers
    (the only ones that count as a result) on the board. No step may follow one that reached
    the target. Raises ``InvalidStepError`` with the index of the first step that can't be played.
    """
    starting = Counter(numbers)
    produced: Counter[int] = Counter()
    played = []

    def take(value: int) -> None:
        if starting[value] > 0:
            starting[value] -= 1
        elif produced[value] > 0:
            produced[value] -= 1
        else:
            raise InvalidStepError(UNAVAILABLE_NUMBER)

    for index, step in enumerate(steps):
        try:
            if index >= MAX_STEPS:
                raise InvalidStepError(TOO_MANY_STEPS)
            if played and played[-1].result == target:
                raise InvalidStepError(TARGET_REACHED)
            take(step.left)
            take(step.right)
            result = apply(step.left, step.op, step.right)
        except InvalidStepError as error:
            raise InvalidStepError(error.reason, index) from None
        produced[result] += 1
        played.append(PlayedStep(step, result))

    remaining = tuple(sorted(produced.elements()))
    final_result = closest(remaining, target)
    distance = None if final_result is None else abs(final_result - target)
    return Replay(
        steps=tuple(played),
        board=tuple(sorted((starting + produced).elements())),
        produced=remaining,
        final_result=final_result,
        distance=distance,
        solved=distance == 0,
    )


def score(distance: int) -> int:
    """Points for a final result ``distance`` away from the target. Higher is better.

    Exact target: 1000. Otherwise ``max(0, 900 - 20 * distance)``: 1 away is 880, 5 away 800,
    20 away 500, and 45 or more away 0.
    """
    if distance == 0:
        return EXACT_SCORE
    return max(0, 900 - 20 * distance)


def difficulty_for(operations: int) -> Difficulty:
    """Easy needs at most 3 operations, medium 4 and hard 5."""
    if not 1 <= operations <= MAX_STEPS:
        raise ValueError(f"A solution has 1 to {MAX_STEPS} operations, not {operations}.")
    if operations <= 3:
        return Difficulty.EASY
    return Difficulty.MEDIUM if operations == 4 else Difficulty.HARD


type _State = tuple[int, ...]


def _moves(larger: int, smaller: int) -> Iterable[tuple[Operator, int]]:
    """The useful steps for a pair. Steps that only throw a number away are skipped:
    ×1 and ÷1 keep ``larger`` and drop the 1, and a − b = b or a ÷ b = b just drop ``larger``.
    Throwing numbers away never helps, since players don't have to use them all."""
    yield Operator.ADD, larger + smaller
    if smaller != 1:
        yield Operator.MUL, larger * smaller
    if larger > smaller and larger - smaller != smaller:
        yield Operator.SUB, larger - smaller
    if smaller != 1 and larger % smaller == 0 and larger // smaller != smaller:
        yield Operator.DIV, larger // smaller


def _path(parents: dict[_State, tuple[_State, PlayedStep] | None], state: _State) -> Solution:
    steps = []
    while (entry := parents[state]) is not None:
        state, played = entry
        steps.append(played)
    return Solution(tuple(reversed(steps)))


def _search(numbers: Sequence[int], target: int | None) -> dict[int, Solution]:
    """Breadth-first search over boards, one level per operation.

    A board is a sorted tuple, so boards with the same numbers are explored once. Level k holds
    the boards first reached with k operations, so the first time a valid target appears it
    was reached with the fewest operations; ``parents`` lets us rebuild those steps. Stops early
    once ``target`` is found; with no target it maps every reachable target to a solution.
    """
    start = tuple(sorted(numbers))
    parents: dict[_State, tuple[_State, PlayedStep] | None] = {start: None}
    found: dict[int, _State] = {}
    frontier = [start]
    for _ in range(MAX_STEPS):
        next_frontier = []
        for state in frontier:
            for i in range(1, len(state)):
                for j in range(i):
                    larger, smaller = state[i], state[j]
                    rest = state[:j] + state[j + 1 : i] + state[i + 1 :]
                    for op, value in _moves(larger, smaller):
                        child = tuple(sorted((*rest, value)))
                        if child in parents:
                            continue
                        parents[child] = (state, PlayedStep(Step(larger, op, smaller), value))
                        next_frontier.append(child)
                        if TARGET_MIN <= value <= TARGET_MAX and value not in found:
                            found[value] = child
                            if value == target:
                                return {value: _path(parents, child)}
        frontier = next_frontier
    if target is not None:
        return {}
    return {value: _path(parents, state) for value, state in sorted(found.items())}


def solve(numbers: Sequence[int], target: int) -> Solution | None:
    """A solution with the fewest operations, or None if the target can't be reached exactly."""
    return _search(numbers, target).get(target)


def reachable(numbers: Sequence[int]) -> dict[int, Solution]:
    """Every valid target these numbers can reach exactly, each with a shortest solution."""
    return _search(numbers, None)


def random_numbers(rng: random.Random) -> tuple[int, ...]:
    """Draw 0 to 4 large numbers, then fill up from the small numbers (two copies of each)."""
    large_count = rng.randint(0, len(LARGE_NUMBERS))
    large = rng.sample(LARGE_NUMBERS, large_count)
    small_pool = [number for number in SMALL_NUMBERS for _ in range(MAX_SMALL_COPIES)]
    small = rng.sample(small_pool, NUMBER_COUNT - large_count)
    return tuple(sorted(large + small))


def generate(
    difficulty: Difficulty, rng: random.Random | None = None, attempts: int = 50
) -> GeneratedPuzzle:
    """A random solvable puzzle whose shortest solution matches the difficulty.

    Draws numbers and picks a target among those whose fewest operations fit the difficulty,
    drawing again when none fit. Pass a seeded ``rng`` for repeatable puzzles. Raises
    ``GenerationFailedError`` if no draw fits in ``attempts`` tries.
    """
    rng = rng or random.Random()
    for _ in range(attempts):
        numbers = random_numbers(rng)
        solutions = reachable(numbers)
        targets = [
            target
            for target, solution in solutions.items()
            if difficulty_for(solution.operations) == difficulty
        ]
        if targets:
            target = rng.choice(targets)
            return GeneratedPuzzle(numbers, target, solutions[target], difficulty)
    raise GenerationFailedError(f"No {difficulty} puzzle found in {attempts} attempts.")
