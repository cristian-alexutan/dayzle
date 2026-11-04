"""Read queries for the Word game app."""

from datetime import date

from apps.puzzles.exceptions import NoPuzzleError
from apps.puzzles.models import Game
from apps.puzzles.selectors import get_playable_puzzle

from .models import Word, WordPuzzle


def get_playable_word_puzzle(day: date) -> WordPuzzle:
    """The day's word, or ``NoPuzzleError`` if the calendar entry has no word yet."""
    puzzle = get_playable_puzzle(Game.WORD, day)
    try:
        return WordPuzzle.objects.select_related("answer", "daily_puzzle").get(daily_puzzle=puzzle)
    except WordPuzzle.DoesNotExist:
        raise NoPuzzleError() from None


def is_known_word(text: str) -> bool:
    return Word.objects.filter(text=text).exists()


def pick_unused_answer() -> Word | None:
    """A random answer never used as a daily word, or any answer once all have been used."""
    answers = Word.objects.filter(is_answer=True).order_by("?")
    return answers.filter(puzzles__isnull=True).first() or answers.first()


def other_days_with_answer(word_puzzle: WordPuzzle) -> list[date]:
    """The other days whose daily word is the same answer."""
    return list(
        WordPuzzle.objects.filter(answer=word_puzzle.answer)
        .exclude(pk=word_puzzle.pk)
        .order_by("daily_puzzle__date")
        .values_list("daily_puzzle__date", flat=True)
    )
