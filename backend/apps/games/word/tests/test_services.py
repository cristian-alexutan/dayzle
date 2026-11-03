import uuid
from datetime import timedelta

import pytest

from apps.common.time import today_in_romania
from apps.games.word import services
from apps.games.word.exceptions import InvalidGuessError, NotAWordError
from apps.games.word.models import Word, WordPuzzle
from apps.puzzles.exceptions import ArchiveUnavailableError, NoPuzzleError
from apps.puzzles.models import Game
from apps.puzzles.tests.factories import DailyPuzzleFactory
from apps.results.exceptions import AlreadyPlayedError
from apps.results.models import GameResult

from .factories import WordFactory, WordPuzzleFactory

pytestmark = pytest.mark.django_db

WRONG_GUESSES = ["tunel", "barză", "verde", "leneș", "câine", "pâine"]


@pytest.fixture
def today():
    """Today's word is "carte"; every word in WRONG_GUESSES is a valid guess."""
    for text in WRONG_GUESSES:
        WordFactory(text=text, is_answer=False)
    WordPuzzleFactory(answer=WordFactory(text="carte"))
    return today_in_romania()


def test_opening_the_game_starts_it_without_guesses(today):
    game = services.open_game(uuid.uuid4(), today)

    assert game.result.status == GameResult.Status.IN_PROGRESS
    assert game.result.details == {}


def test_a_guess_is_colored_and_saved(today):
    guest_id = uuid.uuid4()

    game = services.guess(guest_id, today, "TUNEL")

    assert game.result.details["guesses"] == [
        {"word": "tunel", "colors": ["present", "absent", "absent", "present", "absent"]}
    ]
    assert services.open_game(guest_id, today).result.details == game.result.details


def test_a_correct_guess_finishes_the_game_with_seven_minus_attempts(today):
    guest_id = uuid.uuid4()
    services.guess(guest_id, today, "tunel")

    game = services.guess(guest_id, today, "carte")

    assert game.result.status == GameResult.Status.COMPLETED
    assert game.result.solved is True
    assert game.result.score == 5
    assert game.result.duration_ms is not None


def test_the_sixth_wrong_guess_fails_the_game_with_score_zero(today):
    guest_id = uuid.uuid4()
    for word in WRONG_GUESSES[:-1]:
        assert services.guess(guest_id, today, word).result.status == "in_progress"

    game = services.guess(guest_id, today, WRONG_GUESSES[-1])

    assert game.result.status == GameResult.Status.COMPLETED
    assert game.result.solved is False
    assert game.result.score == 0
    assert len(game.result.details["guesses"]) == 6


@pytest.mark.parametrize(
    ("text", "error"),
    [("cart", InvalidGuessError), ("cart3", InvalidGuessError), ("zzzzz", NotAWordError)],
)
def test_rejected_guesses_do_not_use_an_attempt(today, text, error):
    guest_id = uuid.uuid4()

    with pytest.raises(error):
        services.guess(guest_id, today, text)

    assert services.open_game(guest_id, today).result.details == {}


def test_a_finished_game_cannot_be_played_again(today):
    guest_id = uuid.uuid4()
    services.guess(guest_id, today, "carte")

    with pytest.raises(AlreadyPlayedError):
        services.guess(guest_id, today, "tunel")


def test_a_day_without_a_word_has_no_puzzle():
    DailyPuzzleFactory(game=Game.WORD)  # calendar entry, but no word picked yet

    with pytest.raises(NoPuzzleError):
        services.open_game(uuid.uuid4(), today_in_romania())


def test_only_todays_word_is_playable(today):
    with pytest.raises(ArchiveUnavailableError):
        services.open_game(uuid.uuid4(), today - timedelta(days=1))


def test_import_adds_words_marks_answers_and_can_run_again():
    WordFactory(text="vulpe", is_answer=True)  # marked as an answer in the admin

    first = services.import_words(["carte", "CÂINE", "şarpe", "vulpe", "x"], ["carte"])
    second = services.import_words(["carte", "câine"], ["carte"])

    assert first.added == 3
    assert first.skipped == ["x"]
    assert second.added == 0
    assert set(Word.objects.values_list("text", flat=True)) == {"carte", "câine", "șarpe", "vulpe"}
    assert set(Word.objects.filter(is_answer=True).values_list("text", flat=True)) == {
        "carte",
        "vulpe",
    }


def test_bundled_word_lists_are_valid_and_answers_are_guesses():
    guesses = services._read_word_file(services.GUESSES_FILE)
    answers = services._read_word_file(services.ANSWERS_FILE)

    report = services.import_words(guesses, answers)

    assert report.skipped == []
    assert set(answers) <= set(guesses)


def test_seed_imports_the_lists_and_picks_unused_answers():
    today = today_in_romania()
    first = DailyPuzzleFactory(game=Game.WORD, date=today)
    second = DailyPuzzleFactory(game=Game.WORD, date=today + timedelta(days=1))

    services.seed_puzzle(first)
    services.seed_puzzle(second)

    assert Word.objects.filter(is_answer=True).exists()
    answers = WordPuzzle.objects.values_list("answer", flat=True)
    assert len(set(answers)) == 2
