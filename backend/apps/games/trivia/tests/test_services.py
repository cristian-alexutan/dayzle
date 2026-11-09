import json
import uuid
from datetime import timedelta

import pytest

from apps.common.time import today_in_romania
from apps.games.trivia import services
from apps.games.trivia.exceptions import AlreadyAnsweredError, InvalidAnswerError, OutOfOrderError
from apps.games.trivia.models import Category, Question, TriviaPuzzle
from apps.games.trivia.selectors import pick_questions
from apps.puzzles.exceptions import ArchiveUnavailableError, NoPuzzleError
from apps.puzzles.models import Game
from apps.puzzles.tests.factories import DailyPuzzleFactory
from apps.results.exceptions import AlreadyPlayedError
from apps.results.models import GameResult

from .factories import QuestionFactory, TriviaPuzzleFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def quiz():
    return TriviaPuzzleFactory()


@pytest.fixture
def today(quiz):
    return today_in_romania()


def correct_choice(question: Question) -> int:
    return question.choices.get(is_correct=True).pk


def wrong_choice(question: Question) -> int:
    return question.choices.filter(is_correct=False).first().pk


def play(guest_id, day, questions, right: int):
    """Answer every question, the first ``right`` of them correctly."""
    game = None
    for index, question in enumerate(questions):
        choice = correct_choice(question) if index < right else wrong_choice(question)
        game = services.answer(guest_id, day, question.pk, choice)
    return game


def test_opening_the_game_starts_it_with_five_ordered_questions(quiz, today):
    game = services.open_game(uuid.uuid4(), today)

    assert game.result.status == GameResult.Status.IN_PROGRESS
    assert [q.pk for q in game.questions] == [
        e.question_id for e in quiz.entries.order_by("position")
    ]
    assert game.result.details == {}


def test_an_answer_is_checked_and_reveals_the_correct_choice(today):
    guest_id = uuid.uuid4()
    first = services.open_game(guest_id, today).questions[0]

    game = services.answer(guest_id, today, first.pk, wrong_choice(first))

    assert game.result.details["answers"] == [
        {
            "question": first.pk,
            "choice": wrong_choice(first),
            "correct_choice": correct_choice(first),
            "is_correct": False,
        }
    ]
    assert services.open_game(guest_id, today).result.details == game.result.details


def test_the_fifth_answer_finishes_with_one_point_per_correct_answer(today):
    guest_id = uuid.uuid4()
    questions = services.open_game(guest_id, today).questions

    game = play(guest_id, today, questions, right=3)

    assert game.result.status == GameResult.Status.COMPLETED
    assert game.result.score == 3
    assert game.result.solved is False
    assert game.result.duration_ms is not None


def test_only_five_out_of_five_counts_as_solved(today):
    guest_id = uuid.uuid4()
    questions = services.open_game(guest_id, today).questions

    game = play(guest_id, today, questions, right=5)

    assert game.result.score == 5
    assert game.result.solved is True


def test_a_question_can_be_answered_only_once(today):
    guest_id = uuid.uuid4()
    first = services.open_game(guest_id, today).questions[0]
    services.answer(guest_id, today, first.pk, wrong_choice(first))

    with pytest.raises(AlreadyAnsweredError):
        services.answer(guest_id, today, first.pk, correct_choice(first))


def test_questions_must_be_answered_in_order(today):
    guest_id = uuid.uuid4()
    second = services.open_game(guest_id, today).questions[1]

    with pytest.raises(OutOfOrderError):
        services.answer(guest_id, today, second.pk, correct_choice(second))


def test_a_question_from_another_day_is_invalid(today):
    other = QuestionFactory()

    with pytest.raises(InvalidAnswerError):
        services.answer(uuid.uuid4(), today, other.pk, correct_choice(other))


def test_a_choice_of_another_question_is_invalid(today):
    guest_id = uuid.uuid4()
    first, second = services.open_game(guest_id, today).questions[:2]

    with pytest.raises(InvalidAnswerError):
        services.answer(guest_id, today, first.pk, correct_choice(second))


def test_answering_after_finishing_is_already_played(today):
    guest_id = uuid.uuid4()
    questions = services.open_game(guest_id, today).questions
    play(guest_id, today, questions, right=5)

    with pytest.raises(AlreadyPlayedError):
        services.answer(guest_id, today, questions[0].pk, correct_choice(questions[0]))


def test_each_guest_has_their_own_quiz(today):
    first_guest = uuid.uuid4()
    questions = services.open_game(first_guest, today).questions
    play(first_guest, today, questions, right=5)

    other = services.open_game(uuid.uuid4(), today)

    assert other.result.status == GameResult.Status.IN_PROGRESS


def test_no_quiz_today_is_no_puzzle():
    DailyPuzzleFactory(game=Game.TRIVIA)

    with pytest.raises(NoPuzzleError):
        services.open_game(uuid.uuid4(), today_in_romania())


def test_an_incomplete_quiz_is_no_puzzle():
    TriviaPuzzleFactory(questions=[QuestionFactory() for _ in range(3)])

    with pytest.raises(NoPuzzleError):
        services.open_game(uuid.uuid4(), today_in_romania())


def test_yesterdays_quiz_is_not_playable():
    yesterday = today_in_romania() - timedelta(days=1)
    TriviaPuzzleFactory(daily_puzzle=DailyPuzzleFactory(game=Game.TRIVIA, date=yesterday))

    with pytest.raises(ArchiveUnavailableError):
        services.open_game(uuid.uuid4(), yesterday)


def test_picking_prefers_unused_questions_and_different_categories():
    used = QuestionFactory(category=Category.HISTORY)
    TriviaPuzzleFactory(
        questions=[used, *[QuestionFactory(category=Category.SPORTS) for _ in range(4)]]
    )
    fresh = [QuestionFactory(category=category) for category in Category]

    picked = pick_questions()

    assert len(picked) == 5
    assert set(picked) <= set(fresh)
    assert len({question.category for question in picked}) == 5


def test_picked_questions_go_from_easy_to_hard():
    for difficulty in ["hard", "easy", "medium", "easy", "hard"]:
        QuestionFactory(difficulty=difficulty)

    picked = pick_questions()

    assert [q.difficulty for q in picked] == ["easy", "easy", "medium", "hard", "hard"]


VALID = {
    "question": "Care este capitala Franței?",
    "category": "geography",
    "difficulty": "easy",
    "choices": ["Lyon", "Paris", "Nisa", "Lille"],
    "answer": 1,
}


def test_import_adds_questions_with_their_correct_choice():
    report = services.import_questions([VALID])

    question = Question.objects.get(text=VALID["question"])
    assert report.added == 1
    assert question.choices.get(is_correct=True).text == "Paris"
    assert question.choices.count() == 4


def test_import_is_safe_to_run_again():
    services.import_questions([VALID])

    report = services.import_questions([VALID])

    assert report.added == 0
    assert Question.objects.count() == 1


@pytest.mark.parametrize(
    "change",
    [
        {"category": "music"},
        {"difficulty": "extreme"},
        {"choices": ["Paris", "Lyon", "Nisa"]},
        {"choices": ["Paris", "Paris", "Nisa", "Lille"]},
        {"answer": 4},
        {"question": " "},
        {"question": 42},
        {"question": "x" * 301},
        {"choices": ["Paris", " ", "Nisa", "Lille"]},
        {"choices": ["Paris", 2, "Nisa", "Lille"]},
        {"choices": ["Paris", "x" * 151, "Nisa", "Lille"]},
        {"choices": ["Paris", "paris", "Nisa", "Lille"]},
        {"answer": True},
        {"answer": "1"},
    ],
)
def test_import_skips_invalid_questions(change):
    report = services.import_questions([{**VALID, **change}])

    assert report.added == 0
    assert len(report.skipped) == 1


@pytest.mark.parametrize("bad", ["just text", 7, None, ["a", "list"]])
def test_items_that_are_not_objects_are_skipped(bad):
    report = services.import_questions([bad])

    assert report.added == 0
    assert len(report.skipped) == 1


def test_bad_items_dont_undo_the_good_ones():
    other = {
        **VALID,
        "question": "Care este capitala Italiei?",
        "choices": ["Roma", "Milano", "Napoli", "Torino"],
        "answer": 0,
    }

    report = services.import_questions([VALID, "oops", {**VALID, "question": 42}, other])

    assert report.added == 2
    assert len(report.skipped) == 2
    assert Question.objects.count() == 2


def test_the_bundled_question_file_is_valid():
    items = json.loads(services.QUESTIONS_FILE.read_text(encoding="utf-8"))

    report = services.import_question_file()

    assert report.skipped == []
    assert report.added == len(items)
    assert len({item["category"] for item in items}) == len(Category)


def test_seed_imports_the_bank_and_creates_a_quiz():
    daily_puzzle = DailyPuzzleFactory(game=Game.TRIVIA)

    services.seed_puzzle(daily_puzzle)

    quiz = TriviaPuzzle.objects.get(daily_puzzle=daily_puzzle)
    assert quiz.entries.count() == 5
    assert quiz.questions.values("category").distinct().count() == 5
