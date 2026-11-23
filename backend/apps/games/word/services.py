"""Write operations and business rules for the Word game app."""

import random
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from django.db import transaction

from apps.puzzles.models import DailyPuzzle
from apps.results.exceptions import AlreadyPlayedError
from apps.results.models import GameResult
from apps.results.services import complete, save_progress, start_or_resume

from . import rules
from .exceptions import InvalidGuessError, NotAWordError, NothingToHintError
from .models import Word, WordPuzzle
from .selectors import get_playable_word_puzzle, is_known_word, pick_unused_answer

DATA_DIR = Path(__file__).resolve().parent / "data"
GUESSES_FILE = DATA_DIR / "guesses.txt"
ANSWERS_FILE = DATA_DIR / "answers.txt"


@dataclass(frozen=True)
class WordGame:
    """A player's daily game: their result and the day's word (secret until the game ends)."""

    result: GameResult
    word_puzzle: WordPuzzle


def open_game(guest_id: uuid.UUID, day: date) -> WordGame:
    """Return the player's game for the day, starting it (and its clock) on first open."""
    word_puzzle = get_playable_word_puzzle(day)
    return WordGame(start_or_resume(guest_id, word_puzzle.daily_puzzle), word_puzzle)


def _lock_in_progress(result: GameResult) -> GameResult:
    """Lock the result so two simultaneous moves can't both build on the same state."""
    locked = GameResult.objects.select_for_update().get(pk=result.pk)
    if locked.status == GameResult.Status.COMPLETED:
        raise AlreadyPlayedError()
    return locked


def guess(guest_id: uuid.UUID, day: date, text: str) -> WordGame:
    """Check and color one guess. Invalid and unknown words don't use up an attempt.

    The sixth guess or a correct one finishes the game, scored with ``rules.score`` (hints
    taken lower the score).
    """
    game = open_game(guest_id, day)
    word = rules.normalize(text)
    if not rules.is_well_formed(word):
        raise InvalidGuessError()

    with transaction.atomic():
        result = _lock_in_progress(game.result)
        if not is_known_word(word):
            raise NotAWordError()

        answer = game.word_puzzle.answer.text
        guesses = [
            *result.details.get("guesses", []),
            {"word": word, "colors": rules.color_guess(word, answer)},
        ]
        details = {**result.details, "guesses": guesses}
        solved = word == answer
        if solved or len(guesses) == rules.MAX_ATTEMPTS:
            hints = len(details.get("hints", []))
            score = rules.score(solved=solved, attempts=len(guesses), hints=hints)
            result = complete(result, solved=solved, score=score, details=details)
        else:
            result = save_progress(result, details)
    return WordGame(result, game.word_puzzle)


def hint(guest_id: uuid.UUID, day: date) -> WordGame:
    """Reveal a random letter of the answer the player hasn't discovered yet.

    Hints don't use up an attempt but cost points (``rules.HINT_PENALTY``) if the game is
    solved. ``NothingToHintError`` when every letter is already green, yellow or hinted.
    """
    game = open_game(guest_id, day)
    with transaction.atomic():
        result = _lock_in_progress(game.result)
        guesses = result.details.get("guesses", [])
        hints = result.details.get("hints", [])
        letters = rules.undiscovered_letters(game.word_puzzle.answer.text, guesses, hints)
        if not letters:
            raise NothingToHintError()
        details = {**result.details, "hints": [*hints, random.choice(letters)]}
        result = save_progress(result, details)
    return WordGame(result, game.word_puzzle)


def _read_word_file(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line for line in lines if line.strip() and not line.lstrip().startswith("#")]


@dataclass(frozen=True)
class ImportReport:
    added: int
    answers: int
    skipped: list[str]


@transaction.atomic
def import_words(guesses: Iterable[str], answers: Iterable[str]) -> ImportReport:
    """Add words to the bank and mark the answers. Safe to run again.

    Existing words are kept, and words already marked as answers (e.g. in the admin) stay
    answers. Lines that aren't 5 letters of the alphabet are skipped and reported.
    """
    skipped = []

    def valid(words: Iterable[str]) -> set[str]:
        normalized = set()
        for raw in words:
            word = rules.normalize(raw)
            if rules.is_well_formed(word):
                normalized.add(word)
            else:
                skipped.append(raw.strip())
        return normalized

    answer_words = valid(answers)
    all_words = valid(guesses) | answer_words
    before = Word.objects.count()
    Word.objects.bulk_create(
        [Word(text=text) for text in sorted(all_words)], ignore_conflicts=True, batch_size=2000
    )
    Word.objects.filter(text__in=answer_words, is_answer=False).update(is_answer=True)
    return ImportReport(
        added=Word.objects.count() - before, answers=len(answer_words), skipped=skipped
    )


def import_word_files(
    guesses_path: Path = GUESSES_FILE, answers_path: Path = ANSWERS_FILE
) -> ImportReport:
    return import_words(_read_word_file(guesses_path), _read_word_file(answers_path))


def seed_puzzle(daily_puzzle: DailyPuzzle) -> None:
    """``seed_dev`` hook: give a new day an unused answer, importing the word lists if needed."""
    answer = pick_unused_answer()
    if answer is None:
        import_word_files()
        answer = pick_unused_answer()
    WordPuzzle.objects.create(daily_puzzle=daily_puzzle, answer=answer)
