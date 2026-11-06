"""Read queries for the Trivia game app."""

from datetime import date

from django.db.models import Count, Exists, Max, OuterRef, Prefetch, QuerySet

from apps.puzzles.exceptions import NoPuzzleError
from apps.puzzles.models import Game
from apps.puzzles.selectors import get_playable_puzzle
from apps.results.models import GameResult

from . import rules
from .models import Choice, Question, TriviaPuzzle, TriviaPuzzleQuestion


def has_players(trivia: TriviaPuzzle) -> bool:
    """Whether anyone has opened this quiz. From then on its questions must not change."""
    return GameResult.objects.filter(daily_puzzle_id=trivia.daily_puzzle_id).exists()


def get_playable_trivia_puzzle(day: date) -> TriviaPuzzle:
    """The day's quiz, or ``NoPuzzleError`` if the calendar entry has no complete quiz yet."""
    puzzle = get_playable_puzzle(Game.TRIVIA, day)
    entries = TriviaPuzzleQuestion.objects.select_related("question").prefetch_related(
        Prefetch("question__choices", queryset=Choice.objects.order_by("id"))
    )
    try:
        trivia = (
            TriviaPuzzle.objects.select_related("daily_puzzle")
            .prefetch_related(Prefetch("entries", queryset=entries))
            .get(daily_puzzle=puzzle)
        )
    except TriviaPuzzle.DoesNotExist:
        raise NoPuzzleError() from None
    if len(trivia.entries.all()) != rules.QUESTIONS_PER_QUIZ:
        raise NoPuzzleError()
    return trivia


def ordered_questions(trivia: TriviaPuzzle) -> list[Question]:
    """The quiz's questions by position, using the prefetched entries when available."""
    return [entry.question for entry in trivia.entries.all()]


def playable_questions() -> QuerySet[Question]:
    """Questions that can go in a quiz: 4 choices, one of them correct."""
    correct = Choice.objects.filter(question=OuterRef("pk"), is_correct=True)
    return (
        Question.objects.annotate(choice_count=Count("choices", distinct=True))
        .filter(Exists(correct), choice_count=rules.CHOICES_PER_QUESTION)
        .annotate(uses=Count("entries", distinct=True))
    )


def pick_questions(count: int = rules.QUESTIONS_PER_QUIZ) -> list[Question]:
    """A quiz's worth of questions: least used first, as many categories as possible.

    Returned from easy to hard. Fewer than ``count`` only if the bank is too small.
    """
    candidates = list(playable_questions().order_by("uses", "?"))
    picked, categories = [], set()
    for question in candidates:
        if question.category not in categories:
            picked.append(question)
            categories.add(question.category)
        if len(picked) == count:
            break
    for question in candidates:
        if len(picked) == count:
            break
        if question not in picked:
            picked.append(question)
    return sorted(picked, key=lambda question: rules.DIFFICULTY_ORDER[question.difficulty])


def last_used_dates() -> QuerySet[Question]:
    """Questions annotated with ``last_used``: the latest day they were in a quiz."""
    return Question.objects.annotate(last_used=Max("entries__puzzle__daily_puzzle__date"))


def other_days_with_questions(trivia: TriviaPuzzle) -> dict[str, list[date]]:
    """For each question of this quiz used on other days too: those days."""
    rows = (
        TriviaPuzzleQuestion.objects.filter(question__in=trivia.questions.all())
        .exclude(puzzle=trivia)
        .order_by("puzzle__daily_puzzle__date")
        .values_list("question__text", "puzzle__daily_puzzle__date")
    )
    days: dict[str, list[date]] = {}
    for text, day in rows:
        days.setdefault(text, []).append(day)
    return days
