"""Write operations and business rules for the Math game app."""

import random
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from apps.puzzles.models import DailyPuzzle

from . import rules
from .exceptions import InvalidNumbersError
from .models import MathPuzzle

# seed_dev gives the coming days all three difficulties in turn.
SEED_DIFFICULTIES = (rules.Difficulty.EASY, rules.Difficulty.MEDIUM, rules.Difficulty.HARD)


def steps_to_json(steps: Iterable[rules.PlayedStep]) -> list[dict]:
    """Steps as stored and sent by the API: ``{"left", "op", "right", "result"}``."""
    return [
        {
            "left": played.step.left,
            "op": played.step.op.value,
            "right": played.step.right,
            "result": played.result,
        }
        for played in steps
    ]


@dataclass(frozen=True)
class PuzzleContent:
    """A checked puzzle and what the solver found, ready to store on a ``MathPuzzle``."""

    target: int
    numbers: list[int]
    difficulty: rules.Difficulty
    min_operations: int
    solution: list[dict]

    def apply_to(self, puzzle: MathPuzzle) -> None:
        puzzle.target = self.target
        puzzle.numbers = self.numbers
        puzzle.difficulty = self.difficulty
        puzzle.min_operations = self.min_operations
        puzzle.solution = self.solution


def _content(numbers: Sequence[int], target: int, solution: rules.Solution) -> PuzzleContent:
    return PuzzleContent(
        target=target,
        numbers=list(numbers),
        difficulty=rules.difficulty_for(solution.operations),
        min_operations=solution.operations,
        solution=steps_to_json(solution.steps),
    )


def prepare_puzzle(numbers: Sequence[int], target: int) -> PuzzleContent:
    """Check a puzzle an admin entered and solve it. The solver runs here, never during play.

    Raises ``InvalidNumbersError`` when the numbers or target break the rules, or when the
    target can't be reached exactly.
    """
    rules.validate_numbers(numbers)
    rules.validate_target(target)
    solution = rules.solve(numbers, target)
    if solution is None:
        raise InvalidNumbersError("These numbers can't reach the target exactly.")
    return _content(numbers, target, solution)


def generate_puzzle(
    difficulty: rules.Difficulty, rng: random.Random | None = None
) -> PuzzleContent:
    """A random solvable puzzle of the given difficulty."""
    puzzle = rules.generate(difficulty, rng)
    return _content(puzzle.numbers, puzzle.target, puzzle.solution)


def seed_puzzle(daily_puzzle: DailyPuzzle) -> None:
    """``seed_dev`` hook: a random puzzle, cycling through the difficulties by date."""
    difficulty = SEED_DIFFICULTIES[daily_puzzle.date.toordinal() % len(SEED_DIFFICULTIES)]
    puzzle = MathPuzzle(daily_puzzle=daily_puzzle)
    generate_puzzle(difficulty).apply_to(puzzle)
    puzzle.save()
