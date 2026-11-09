from datetime import timedelta

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.games.trivia.models import Category, Question, TriviaPuzzle
from apps.puzzles.models import Game
from apps.puzzles.tests.factories import DailyPuzzleFactory
from apps.results.tests.factories import GameResultFactory

from .factories import QuestionFactory, TriviaPuzzleFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "name", ["games_trivia_question_changelist", "games_trivia_triviapuzzle_changelist"]
)
def test_admin_pages_load(admin_client, name):
    TriviaPuzzleFactory()

    assert admin_client.get(reverse(f"admin:{name}")).status_code == 200


def question_form(correct: list[bool], texts=("A", "B", "C", "D")) -> dict:
    data = {
        "text": "Care este capitala Franței?",
        "category": Category.GEOGRAPHY,
        "difficulty": "easy",
        "choices-TOTAL_FORMS": "4",
        "choices-INITIAL_FORMS": "0",
        "choices-MIN_NUM_FORMS": "4",
        "choices-MAX_NUM_FORMS": "4",
    }
    for index, (text, is_correct) in enumerate(zip(texts, correct, strict=True)):
        data[f"choices-{index}-text"] = text
        if is_correct:
            data[f"choices-{index}-is_correct"] = "on"
    return data


def test_a_question_needs_exactly_one_correct_choice(admin_client):
    url = reverse("admin:games_trivia_question_add")

    admin_client.post(url, question_form([True, True, False, False]))
    assert not Question.objects.exists()

    admin_client.post(url, question_form([False, True, False, False]))
    assert Question.objects.get().choices.get(is_correct=True).text == "B"


def quiz_form(daily_puzzle, questions) -> dict:
    data = {
        "daily_puzzle": daily_puzzle.pk,
        "entries-TOTAL_FORMS": str(len(questions)),
        "entries-INITIAL_FORMS": "0",
        "entries-MIN_NUM_FORMS": "5",
        "entries-MAX_NUM_FORMS": "5",
    }
    for index, question in enumerate(questions):
        data[f"entries-{index}-question"] = question.pk
        data[f"entries-{index}-position"] = index + 1
    return data


def test_a_quiz_needs_five_different_questions(admin_client):
    daily_puzzle = DailyPuzzleFactory(game=Game.TRIVIA)
    question = QuestionFactory()
    url = reverse("admin:games_trivia_triviapuzzle_add")

    admin_client.post(url, quiz_form(daily_puzzle, [question] * 5))
    admin_client.post(url, quiz_form(daily_puzzle, [QuestionFactory() for _ in range(4)]))

    assert not TriviaPuzzle.objects.exists()


def test_admin_warns_about_few_categories_and_reused_questions(admin_client):
    used = TriviaPuzzleFactory()
    tomorrow = DailyPuzzleFactory(game=Game.TRIVIA, date=used.daily_puzzle.date + timedelta(days=1))
    questions = [used.questions.first(), *[QuestionFactory() for _ in range(4)]]

    response = admin_client.post(
        reverse("admin:games_trivia_triviapuzzle_add"),
        quiz_form(tomorrow, questions),
        follow=True,
    )

    assert TriviaPuzzle.objects.filter(daily_puzzle=tomorrow).exists()
    warnings = [str(m) for m in get_messages(response.wsgi_request)]
    assert any("covers only 2 categories" in w for w in warnings)
    assert any("is also used on" in w for w in warnings)


def edit_question_form(question: Question, correct_index: int) -> dict:
    """The change form of a saved question, with the tick moved to ``correct_index``."""
    data = {
        "text": question.text,
        "category": question.category,
        "difficulty": question.difficulty,
        "choices-TOTAL_FORMS": "4",
        "choices-INITIAL_FORMS": "4",
        "choices-MIN_NUM_FORMS": "4",
        "choices-MAX_NUM_FORMS": "4",
    }
    for index, choice in enumerate(question.choices.order_by("id")):
        data[f"choices-{index}-id"] = choice.pk
        data[f"choices-{index}-question"] = question.pk
        data[f"choices-{index}-text"] = choice.text
        if index == correct_index:
            data[f"choices-{index}-is_correct"] = "on"
    return data


@pytest.mark.parametrize("correct_index", [1, 3])
def test_the_correct_choice_of_a_saved_question_can_be_changed(admin_client, correct_index):
    question = QuestionFactory()  # "A" is correct
    url = reverse("admin:games_trivia_question_change", args=[question.pk])

    response = admin_client.post(url, edit_question_form(question, correct_index))

    assert response.status_code == 302
    correct = question.choices.get(is_correct=True)
    assert correct.text == "ABCD"[correct_index]


def edit_quiz_form(quiz: TriviaPuzzle, rows: list[tuple[int, int]]) -> dict:
    """The change form of a saved quiz; ``rows`` gives each saved row's (position, question)."""
    data = {
        "daily_puzzle": quiz.daily_puzzle.pk,
        "entries-TOTAL_FORMS": "5",
        "entries-INITIAL_FORMS": "5",
        "entries-MIN_NUM_FORMS": "5",
        "entries-MAX_NUM_FORMS": "5",
    }
    for index, (entry, (position, question)) in enumerate(
        zip(quiz.entries.order_by("position"), rows, strict=True)
    ):
        data[f"entries-{index}-id"] = entry.pk
        data[f"entries-{index}-puzzle"] = quiz.pk
        data[f"entries-{index}-position"] = position
        data[f"entries-{index}-question"] = question
    return data


def saved_order(quiz: TriviaPuzzle) -> list[int]:
    return list(quiz.entries.order_by("position").values_list("question_id", flat=True))


def test_two_positions_of_a_saved_quiz_can_be_swapped(admin_client):
    quiz = TriviaPuzzleFactory()
    first, second, *rest = saved_order(quiz)
    rows = [(2, first), (1, second), *[(i, q) for i, q in enumerate(rest, start=3)]]

    response = admin_client.post(
        reverse("admin:games_trivia_triviapuzzle_change", args=[quiz.pk]),
        edit_quiz_form(quiz, rows),
    )

    assert response.status_code == 302
    assert saved_order(quiz) == [second, first, *rest]


def test_two_questions_of_a_saved_quiz_can_be_swapped(admin_client):
    quiz = TriviaPuzzleFactory()
    first, second, *rest = saved_order(quiz)
    rows = [(1, second), (2, first), *[(i, q) for i, q in enumerate(rest, start=3)]]

    response = admin_client.post(
        reverse("admin:games_trivia_triviapuzzle_change", args=[quiz.pk]),
        edit_quiz_form(quiz, rows),
    )

    assert response.status_code == 302
    assert saved_order(quiz) == [second, first, *rest]


def test_a_quiz_question_can_be_replaced_before_anyone_plays(admin_client):
    quiz = TriviaPuzzleFactory()
    order = saved_order(quiz)
    new = QuestionFactory()
    rows = [(1, new.pk), *[(i, q) for i, q in enumerate(order[1:], start=2)]]

    admin_client.post(
        reverse("admin:games_trivia_triviapuzzle_change", args=[quiz.pk]),
        edit_quiz_form(quiz, rows),
    )

    assert saved_order(quiz) == [new.pk, *order[1:]]


def test_a_quiz_is_read_only_once_players_have_started(admin_client):
    quiz = TriviaPuzzleFactory()
    GameResultFactory(daily_puzzle=quiz.daily_puzzle)
    order = saved_order(quiz)
    url = reverse("admin:games_trivia_triviapuzzle_change", args=[quiz.pk])

    page = admin_client.get(url)
    rows = [(1, QuestionFactory().pk), *[(i, q) for i, q in enumerate(order[1:], start=2)]]
    edit = admin_client.post(url, edit_quiz_form(quiz, rows))
    delete = admin_client.post(
        reverse("admin:games_trivia_triviapuzzle_delete", args=[quiz.pk]), {"post": "yes"}
    )

    warnings = [str(m) for m in get_messages(page.wsgi_request)]
    assert any("already started this quiz" in w for w in warnings)
    assert edit.status_code == 403
    assert delete.status_code == 403
    assert saved_order(quiz) == order
