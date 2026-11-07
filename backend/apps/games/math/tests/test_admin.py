import pytest
from django.urls import reverse

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


def test_a_started_puzzle_can_no_longer_change(admin_client):
    puzzle = MathPuzzleFactory()
    GameResultFactory(daily_puzzle=puzzle.daily_puzzle)

    response = admin_client.post(
        change_url(puzzle), form_data(puzzle.daily_puzzle, 576, "2, 2, 3, 3, 4, 4")
    )

    assert "Players have already started this puzzle" in response.content.decode()
    puzzle.refresh_from_db()
    assert puzzle.target == 253


def test_an_unstarted_puzzle_can_still_change(admin_client):
    puzzle = MathPuzzleFactory()

    response = admin_client.post(
        change_url(puzzle), form_data(puzzle.daily_puzzle, 576, "2, 2, 3, 3, 4, 4")
    )

    assert response.status_code == 302
    puzzle.refresh_from_db()
    assert (puzzle.target, puzzle.min_operations) == (576, 5)
