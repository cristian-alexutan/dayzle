"""Write operations and business rules for the Math game app."""

import random
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date

from apps.puzzles.models import DailyPuzzle
from apps.results.exceptions import AlreadyPlayedError
from apps.results.models import GameResult
from apps.results.services import complete, save_progress, start_or_resume

from . import rules
from .exceptions import GenerationFailedError, InvalidNumbersError, NoStepsError
from .models import MathPuzzle
from .selectors import get_playable_math_puzzle

# seed_dev gives the coming days all three difficulties in turn.
SEED_DIFFICULTIES = (rules.Difficulty.EASY, rules.Difficulty.MEDIUM, rules.Difficulty.HARD)
# Used by seed_dev if the generator fails, so a day is never left without content.
FALLBACK_NUMBERS = (2, 2, 3, 3, 4, 4)
FALLBACK_TARGET = 576


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
    """``seed_dev`` hook: a random puzzle, cycling through the difficulties by date.

    If the generator fails, the day gets a fixed puzzle instead: ``seed_dev`` skips days it has
    already created, so a failure here would leave the day empty for good.
    """
    difficulty = SEED_DIFFICULTIES[daily_puzzle.date.toordinal() % len(SEED_DIFFICULTIES)]
    try:
        content = generate_puzzle(difficulty)
    except GenerationFailedError:
        content = prepare_puzzle(FALLBACK_NUMBERS, FALLBACK_TARGET)
    puzzle = MathPuzzle(daily_puzzle=daily_puzzle)
    content.apply_to(puzzle)
    puzzle.save()


@dataclass(frozen=True)
class MathGame:
    """A player's daily game: their result and the day's puzzle (solution secret until the end)."""

    result: GameResult
    math_puzzle: MathPuzzle


def open_game(guest_id: uuid.UUID, day: date) -> MathGame:
    """Return the player's game for the day, starting it (and its clock) on first open."""
    math_puzzle = get_playable_math_puzzle(day)
    return MathGame(start_or_resume(guest_id, math_puzzle.daily_puzzle), math_puzzle)


def _replay_for(game: MathGame, steps: Sequence[rules.Step]) -> rules.Replay:
    """Replay the steps from the puzzle's starting numbers; nothing the browser computed counts.

    A finished game is reported as already played before its steps are even looked at.
    """
    if game.result.status == GameResult.Status.COMPLETED:
        raise AlreadyPlayedError()
    return rules.replay(game.math_puzzle.numbers, game.math_puzzle.target, steps)


def _finish(game: MathGame, replay: rules.Replay) -> MathGame:
    """Complete the game, scored with ``rules.score`` on the distance to the target.

    ``details`` keeps the steps, final result, distance and number of operations.
    """
    details = {
        "steps": steps_to_json(replay.steps),
        "final_result": replay.final_result,
        "distance": replay.distance,
        "operations": len(replay.steps),
    }
    result = complete(
        game.result, solved=replay.solved, score=rules.score(replay.distance), details=details
    )
    return MathGame(result, game.math_puzzle)


def save_steps(guest_id: uuid.UUID, day: date, steps: Sequence[rules.Step]) -> MathGame:
    """Save the board after a step, undo or reset, so a refresh restores it.

    The steps replace the saved ones. A step that reaches the target exactly finishes the game
    right away, as Word does on the right guess, so a solved game isn't lost if the page closes
    before a submit. An invalid step raises ``InvalidStepError`` and nothing is saved, so the
    game goes on from the last valid board.
    """
    game = open_game(guest_id, day)
    replay = _replay_for(game, steps)
    if replay.solved:
        return _finish(game, replay)
    result = save_progress(game.result, {"steps": steps_to_json(replay.steps)})
    return MathGame(result, game.math_puzzle)


def submit(guest_id: uuid.UUID, day: date, steps: Sequence[rules.Step]) -> MathGame:
    """Finish the game with the player's final steps, e.g. when they can't get any closer.

    The final result is the computed number closest to the target; at least one step is needed.
    """
    game = open_game(guest_id, day)
    replay = _replay_for(game, steps)
    if not steps:
        raise NoStepsError()
    return _finish(game, replay)
