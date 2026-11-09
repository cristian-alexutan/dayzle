"""Rules of the Trivia game that need no database: quiz shape and scoring."""

from collections.abc import Iterable

QUESTIONS_PER_QUIZ = 5
CHOICES_PER_QUESTION = 4
# A daily quiz should cover at least this many categories; the admin warns below it.
MIN_CATEGORIES = 4
# Order of the questions in a generated quiz: from easy to hard.
DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}


def score(answers: Iterable[dict]) -> int:
    """One point per correct answer, so 0 to 5. Ties are broken by ``duration_ms``."""
    return sum(1 for answer in answers if answer["is_correct"])


def is_perfect(points: int) -> bool:
    """A quiz counts as solved only with every answer right."""
    return points == QUESTIONS_PER_QUIZ
