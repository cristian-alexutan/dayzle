from datetime import timedelta

import pytest
from django.urls import reverse

from apps.common.time import today_in_romania
from apps.games.math import rules
from apps.games.math.exceptions import GenerationFailedError
from apps.games.math.models import MathPuzzle
from apps.puzzles.models import Game
from apps.puzzles.tests.factories import DailyPuzzleFactory
from apps.results.tests.factories import GameResultFactory

from .factories import MathPuzzleFactory

pytestmark = pytest.mark.django_db

ADD_URL = reverse("admin:games_math_mathpuzzle_add")


def change_url(puzzle):
    return reverse("admin:games_math_mathpuzzle_change", args=[puzzle.pk])


def tomorrow():
    return DailyPuzzleFactory(game=Game.MATH, date=today_in_romania() + timedelta(days=1))


def form_data(daily_puzzle, target="", numbers="", generate=""):
    return {
        "daily_puzzle": daily_puzzle.pk,
        "target": target,
        "numbers": numbers,
        "generate": generate,
    }


@pytest.mark.parametrize("url", [ADD_URL, reverse("admin:games_math_mathpuzzle_changelist")])
def test_admin_pages_load(admin_client, url):
    MathPuzzleFactory()

    assert admin_client.get(url).status_code == 200


def test_change_page_shows_the_example_solution(admin_client):
    puzzle = MathPuzzleFactory()

    response = admin_client.get(change_url(puzzle))

    assert "100 * 2 = 200; 50 + 3 = 53; 200 + 53 = 253" in response.content.decode()


def test_saving_stores_what_the_solver_found(admin_client):
    day = DailyPuzzleFactory(game=Game.MATH)

    response = admin_client.post(ADD_URL, form_data(day, 576, "2, 2, 3, 3, 4, 4"))

    assert response.status_code == 302
    puzzle = MathPuzzle.objects.get()
    assert puzzle.numbers == [2, 2, 3, 3, 4, 4]
    assert (puzzle.difficulty, puzzle.min_operations) == ("hard", 5)
    assert puzzle.solution[-1]["result"] == 576


@pytest.mark.parametrize(
    ("target", "numbers", "generate", "message"),
    [
        (101, "1, 1, 2, 2, 3, 3", "", "can&#x27;t reach the target exactly"),
        (200, "25, 25, 1, 2, 3, 4", "", "25 can appear at most once"),
        (200, "25, x, 1, 2, 3, 4", "", "separated by commas"),
        (200, "", "", "Enter both the target and the 6 numbers"),
        ("", "", "", "or pick a difficulty"),
        (200, "1, 2, 3, 4, 5, 25", "easy", "Clear the target and numbers"),
    ],
)
def test_broken_puzzles_are_rejected(admin_client, target, numbers, generate, message):
    day = DailyPuzzleFactory(game=Game.MATH)

    response = admin_client.post(ADD_URL, form_data(day, target, numbers, generate))

    assert response.status_code == 200
    assert message in response.content.decode()
    assert not MathPuzzle.objects.exists()


def test_a_difficulty_generates_the_puzzle(admin_client):
    day = DailyPuzzleFactory(game=Game.MATH)

    response = admin_client.post(ADD_URL, form_data(day, generate="medium"))

    assert response.status_code == 302
    puzzle = MathPuzzle.objects.get()
    assert (puzzle.difficulty, puzzle.min_operations) == ("medium", 4)
    assert 101 <= puzzle.target <= 999
    assert len(puzzle.numbers) == 6


def test_a_failed_generation_is_a_form_error_not_a_crash(admin_client, monkeypatch):
    def fail(difficulty, rng=None):
        raise GenerationFailedError()

    monkeypatch.setattr(rules, "generate", fail)
    day = DailyPuzzleFactory(game=Game.MATH)

    response = admin_client.post(ADD_URL, form_data(day, generate="hard"))

    assert response.status_code == 200
    assert "No puzzle of this difficulty was found" in response.content.decode()
    assert not MathPuzzle.objects.exists()


@pytest.fixture
def started_puzzle():
    puzzle = MathPuzzleFactory()
    GameResultFactory(daily_puzzle=puzzle.daily_puzzle)
    return puzzle


def test_a_started_puzzle_is_shown_read_only(admin_client, started_puzzle):
    content = admin_client.get(change_url(started_puzzle)).content.decode()

    assert 'name="target"' not in content
    assert 'name="numbers"' not in content
    assert 'name="generate"' not in content
    assert '<div class="readonly">[1, 2, 3, 25, 50, 100]</div>' in content
    assert "deletelink" not in content


def test_a_started_puzzle_can_no_longer_change(admin_client, started_puzzle):
    other_day = tomorrow()

    admin_client.post(change_url(started_puzzle), form_data(other_day, 576, "2, 2, 3, 3, 4, 4"))

    started_puzzle.refresh_from_db()
    assert started_puzzle.target == 253
    assert started_puzzle.numbers == [1, 2, 3, 25, 50, 100]
    assert started_puzzle.daily_puzzle != other_day


def test_a_started_puzzle_cannot_be_deleted(admin_client, started_puzzle):
    delete_url = reverse("admin:games_math_mathpuzzle_delete", args=[started_puzzle.pk])

    assert admin_client.post(delete_url, {"post": "yes"}).status_code == 403
    assert MathPuzzle.objects.filter(pk=started_puzzle.pk).exists()


def test_a_started_puzzle_cannot_be_deleted_from_the_list(admin_client, started_puzzle):
    changelist_url = reverse("admin:games_math_mathpuzzle_changelist")
    action = {"action": "delete_selected", "_selected_action": [started_puzzle.pk], "post": "yes"}

    admin_client.post(changelist_url, action)

    assert MathPuzzle.objects.filter(pk=started_puzzle.pk).exists()


def test_an_unstarted_puzzle_can_be_deleted(admin_client):
    puzzle = MathPuzzleFactory()
    delete_url = reverse("admin:games_math_mathpuzzle_delete", args=[puzzle.pk])

    assert admin_client.post(delete_url, {"post": "yes"}).status_code == 302
    assert not MathPuzzle.objects.exists()


def test_a_puzzle_cannot_be_added_to_a_day_with_players(admin_client):
    day = DailyPuzzleFactory(game=Game.MATH)
    GameResultFactory(daily_puzzle=day)

    response = admin_client.post(ADD_URL, form_data(day, 576, "2, 2, 3, 3, 4, 4"))

    assert "Players have already started this day" in response.content.decode()
    assert not MathPuzzle.objects.exists()


def test_a_puzzle_cannot_move_to_a_day_with_players(admin_client):
    puzzle = MathPuzzleFactory()
    played_day = tomorrow()
    GameResultFactory(daily_puzzle=played_day)

    response = admin_client.post(
        change_url(puzzle), form_data(played_day, 253, "1, 2, 3, 25, 50, 100")
    )

    assert "Players have already started this day" in response.content.decode()
    puzzle.refresh_from_db()
    assert puzzle.daily_puzzle != played_day


def test_an_unstarted_puzzle_can_still_change(admin_client):
    puzzle = MathPuzzleFactory()

    response = admin_client.post(
        change_url(puzzle), form_data(puzzle.daily_puzzle, 576, "2, 2, 3, 3, 4, 4")
    )

    assert response.status_code == 302
    puzzle.refresh_from_db()
    assert (puzzle.target, puzzle.min_operations) == (576, 5)
