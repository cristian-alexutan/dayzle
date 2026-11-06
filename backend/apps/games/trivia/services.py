"""Write operations and business rules for the Trivia game app."""

import json
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from django.db import transaction

from apps.puzzles.models import DailyPuzzle
from apps.results.exceptions import AlreadyPlayedError
from apps.results.models import GameResult
from apps.results.services import complete, save_progress, start_or_resume

from . import rules
from .exceptions import AlreadyAnsweredError, InvalidAnswerError, OutOfOrderError
from .models import Category, Choice, Difficulty, Question, TriviaPuzzle, TriviaPuzzleQuestion
from .selectors import get_playable_trivia_puzzle, ordered_questions, pick_questions

QUESTIONS_FILE = Path(__file__).resolve().parent / "data" / "questions.json"
QUESTION_MAX_LENGTH = Question._meta.get_field("text").max_length
CHOICE_MAX_LENGTH = Choice._meta.get_field("text").max_length


@dataclass(frozen=True)
class TriviaGame:
    """A player's daily quiz: their result and the day's questions, in order."""

    result: GameResult
    puzzle: TriviaPuzzle
    questions: list[Question]


def open_game(guest_id: uuid.UUID, day: date) -> TriviaGame:
    """Return the player's quiz for the day, starting it (and its clock) on first open."""
    puzzle = get_playable_trivia_puzzle(day)
    result = start_or_resume(guest_id, puzzle.daily_puzzle)
    return TriviaGame(result, puzzle, ordered_questions(puzzle))


def answer(guest_id: uuid.UUID, day: date, question_id: int, choice_id: int) -> TriviaGame:
    """Check the answer to the next question and reveal the correct choice.

    Questions are answered in order, once each. The fifth answer finishes the game with
    ``rules.score`` (one point per correct answer); only 5 out of 5 counts as solved.
    """
    game = open_game(guest_id, day)
    question = next((q for q in game.questions if q.pk == question_id), None)
    if question is None:
        raise InvalidAnswerError()
    choices = list(question.choices.all())
    chosen = next((c for c in choices if c.pk == choice_id), None)
    if chosen is None:
        raise InvalidAnswerError()
    correct = next(c for c in choices if c.is_correct)

    with transaction.atomic():
        # Lock the result so two simultaneous answers can't both count for the same question.
        result = GameResult.objects.select_for_update().get(pk=game.result.pk)
        if result.status == GameResult.Status.COMPLETED:
            raise AlreadyPlayedError()
        answers = result.details.get("answers", [])
        answered = {given["question"] for given in answers}
        if question_id in answered:
            raise AlreadyAnsweredError()
        next_question = next(q for q in game.questions if q.pk not in answered)
        if next_question.pk != question_id:
            raise OutOfOrderError()

        answers = [
            *answers,
            {
                "question": question_id,
                "choice": choice_id,
                "correct_choice": correct.pk,
                "is_correct": chosen.pk == correct.pk,
            },
        ]
        details = {"answers": answers}
        if len(answers) == len(game.questions):
            points = rules.score(answers)
            result = complete(
                result, solved=rules.is_perfect(points), score=points, details=details
            )
        else:
            result = save_progress(result, details)
    return TriviaGame(result, game.puzzle, game.questions)


@transaction.atomic
def create_quiz(daily_puzzle: DailyPuzzle, questions: Sequence[Question]) -> TriviaPuzzle:
    """Make the day's quiz from these questions, in this order."""
    puzzle = TriviaPuzzle.objects.create(daily_puzzle=daily_puzzle)
    TriviaPuzzleQuestion.objects.bulk_create(
        TriviaPuzzleQuestion(puzzle=puzzle, question=question, position=position)
        for position, question in enumerate(questions, start=1)
    )
    return puzzle


@dataclass(frozen=True)
class ImportReport:
    added: int
    skipped: list[str]


def _text_problem(value: object, field: str, max_length: int) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return f"{field} must be non-empty text"
    if len(value.strip()) > max_length:
        return f"{field} is longer than {max_length} characters"
    return None


def _problem(item: object) -> str | None:
    """Why an item of the import file can't be used as a question, or None if it's fine."""
    if not isinstance(item, dict):
        return "not a question object"
    problem = _text_problem(item.get("question"), "question", QUESTION_MAX_LENGTH)
    if problem:
        return problem
    if item.get("category") not in Category.values:
        return f"unknown category {item.get('category')!r}"
    if item.get("difficulty") not in Difficulty.values:
        return f"unknown difficulty {item.get('difficulty')!r}"
    choices = item.get("choices")
    if not isinstance(choices, list) or len(choices) != rules.CHOICES_PER_QUESTION:
        return f"needs a list of {rules.CHOICES_PER_QUESTION} choices"
    for choice in choices:
        problem = _text_problem(choice, "each choice", CHOICE_MAX_LENGTH)
        if problem:
            return problem
    if len({choice.strip().lower() for choice in choices}) != rules.CHOICES_PER_QUESTION:
        return "the choices must be different"
    answer = item.get("answer")
    # bool is an int in Python, so True would otherwise pass as index 1.
    if isinstance(answer, bool) or answer not in range(rules.CHOICES_PER_QUESTION):
        return (
            f"answer must be the index (0-{rules.CHOICES_PER_QUESTION - 1}) of the correct choice"
        )
    return None


def _label(item: object) -> str:
    text = item.get("question") if isinstance(item, dict) else None
    return text.strip()[:80] if isinstance(text, str) and text.strip() else repr(item)[:80]


def import_questions(items: Iterable[object]) -> ImportReport:
    """Add questions to the bank. Safe to run again: questions already there are kept as is.

    Each item has ``question``, ``category``, ``difficulty``, 4 ``choices`` and ``answer``
    (the index of the correct choice). Invalid items are skipped and reported, and never
    undo the valid ones: each question is saved on its own.
    """
    added, skipped = 0, []
    existing = set(Question.objects.values_list("text", flat=True))
    for number, item in enumerate(items, start=1):
        problem = _problem(item)
        if problem:
            skipped.append(f"#{number} {_label(item)}: {problem}")
            continue
        text = item["question"].strip()
        if text in existing:
            continue
        with transaction.atomic():
            question = Question.objects.create(
                text=text, category=item["category"], difficulty=item["difficulty"]
            )
            Choice.objects.bulk_create(
                Choice(question=question, text=choice.strip(), is_correct=index == item["answer"])
                for index, choice in enumerate(item["choices"])
            )
        existing.add(text)
        added += 1
    return ImportReport(added=added, skipped=skipped)


def import_question_file(path: Path = QUESTIONS_FILE) -> ImportReport:
    return import_questions(json.loads(path.read_text(encoding="utf-8")))


def seed_puzzle(daily_puzzle: DailyPuzzle) -> None:
    """``seed_dev`` hook: give a new day 5 questions, importing the question bank if needed."""
    questions = pick_questions()
    if len(questions) < rules.QUESTIONS_PER_QUIZ:
        import_question_file()
        questions = pick_questions()
    create_quiz(daily_puzzle, questions)
