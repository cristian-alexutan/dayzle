"""Rules of the Trivia game that need no database: quiz shape and scoring."""

from collections.abc import Iterable

QUESTIONS_PER_QUIZ = 5
CHOICES_PER_QUESTION = 4
# A daily quiz should cover at least this many categories; the admin warns below it.
MIN_CATEGORIES = 4
# Order of the questions in a generated quiz: from easy to hard.
DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}


# A hint (50/50) removes this many wrong choices from a question, once per question.
CHOICES_REMOVED_BY_HINT = 2

# Scores are stored in half points, so a hinted answer can be worth half a point and the shared
# ``GameResult.score`` stays a whole number: a correct answer is 2, a hinted correct answer 1.
# The API divides by ``SCORE_SCALE`` to show 0 to 5, e.g. 3.5.
SCORE_SCALE = 2
POINTS_PER_ANSWER = 2
POINTS_PER_HINTED_ANSWER = 1


def score(answers: Iterable[dict]) -> int:
    """The score in half points, 0 to 10: 2 per correct answer, 1 if a hint was used on it.

    Ties are broken by ``duration_ms``.
    """
    return sum(
        POINTS_PER_HINTED_ANSWER if answer.get("hinted") else POINTS_PER_ANSWER
        for answer in answers
        if answer["is_correct"]
    )


def is_perfect(answers: Iterable[dict]) -> bool:
    """A quiz counts as solved with every answer right, hints or not."""
    answers = list(answers)
    return len(answers) == QUESTIONS_PER_QUIZ and all(answer["is_correct"] for answer in answers)
