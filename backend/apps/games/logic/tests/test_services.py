import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.common.time import today_in_romania
from apps.games.logic import rules, services
from apps.games.logic.exceptions import InvalidCellError
from apps.puzzles.exceptions import NoPuzzleError
from apps.results.exceptions import AlreadyPlayedError
from apps.results.models import GameResult

from .factories import LogicPuzzleFactory

pytestmark = pytest.mark.django_db

# The demo level's solution, as cells: (0, 2), (1, 0), (2, 4), (3, 1), (4, 3), (5, 5).
SOLUTION_CELLS = list(enumerate(rules.DEMO_SOLUTION))


@pytest.fixture
def today():
    LogicPuzzleFactory()
    return today_in_romania()


@pytest.fixture
def guest_id():
    return uuid.uuid4()


def place_all(guest_id, day):
    outcome = None
    for row, col in SOLUTION_CELLS:
        outcome = services.place_sun(guest_id, day, row, col)
    return outcome


def test_opening_the_game_starts_it_with_an_empty_board(today, guest_id):
    game = services.open_game(guest_id, today)

    assert game.result.status == GameResult.Status.IN_PROGRESS
    assert game.result.details == {}


def test_a_correct_sun_stays_on_the_board(today, guest_id):
    outcome = services.place_sun(guest_id, today, 0, 2)

    assert outcome.correct is True
    assert outcome.conflicts == []
    assert outcome.game.result.details["suns"] == [[0, 2]]
    assert outcome.game.result.details["moves"] == [True]


def test_a_wrong_sun_is_not_kept_and_counts_as_a_mistake(today, guest_id):
    outcome = services.place_sun(guest_id, today, 0, 0)

    assert outcome.correct is False
    assert outcome.game.result.details["suns"] == []
    assert outcome.game.result.details["moves"] == [False]


def test_a_wrong_sun_reports_the_suns_it_conflicts_with(today, guest_id):
    services.place_sun(guest_id, today, 0, 2)

    # (0, 3) is on the same row and in the same region as the sun on (0, 2).
    outcome = services.place_sun(guest_id, today, 0, 3)

    assert outcome.correct is False
    assert outcome.conflicts == [(0, 2)]


def test_a_wrong_sun_with_no_visible_conflict_is_still_a_mistake(today, guest_id):
    outcome = services.place_sun(guest_id, today, 0, 0)

    assert outcome.correct is False
    assert outcome.conflicts == []


def test_placing_a_sun_removes_the_x_mark_of_its_cell(today, guest_id):
    services.save_marks(guest_id, today, [(0, 2), (0, 0)])

    outcome = services.place_sun(guest_id, today, 0, 2)

    assert outcome.game.result.details["marks"] == [[0, 0]]


def test_a_sun_cannot_be_placed_twice(today, guest_id):
    services.place_sun(guest_id, today, 0, 2)

    with pytest.raises(InvalidCellError):
        services.place_sun(guest_id, today, 0, 2)


def test_a_sun_outside_the_grid_is_rejected_and_not_counted(today, guest_id):
    with pytest.raises(InvalidCellError):
        services.place_sun(guest_id, today, 6, 0)

    assert services.open_game(guest_id, today).result.details.get("moves", []) == []


def test_the_last_correct_sun_finishes_the_game_with_a_score(today, guest_id):
    outcome = place_all(guest_id, today)

    result = outcome.game.result
    assert result.status == GameResult.Status.COMPLETED
    assert result.solved is True
    assert result.score == rules.score([True] * 6, 6, result.duration_ms)


def test_the_score_uses_the_moves_and_the_measured_duration(today, guest_id):
    services.place_sun(guest_id, today, 0, 0)  # one mistake before starting
    # Pretend the player has already played for 2 minutes.
    result = GameResult.objects.get(guest_id=guest_id)
    result.active_ms = 2 * 60_000
    result.last_active_at = timezone.now()
    result.save()

    outcome = place_all(guest_id, today)

    result = outcome.game.result
    assert 2 * 60_000 <= result.duration_ms < 2 * 60_000 + 5_000
    # A mistake first, then 6 correct suns in a row: the full combo.
    assert result.details["moves"] == [False] + [True] * 6
    assert result.score == rules.score(result.details["moves"], 6, result.duration_ms)
    assert 895 <= result.score <= 900


def test_playing_after_finishing_is_already_played(today, guest_id):
    place_all(guest_id, today)

    with pytest.raises(AlreadyPlayedError):
        services.place_sun(guest_id, today, 0, 0)
    with pytest.raises(AlreadyPlayedError):
        services.save_marks(guest_id, today, [(0, 0)])


def test_marks_are_saved_without_duplicates_or_cells_with_suns(today, guest_id):
    services.place_sun(guest_id, today, 0, 2)

    game = services.save_marks(guest_id, today, [(1, 1), (1, 1), (0, 2), (3, 3)])

    assert game.result.details["marks"] == [[1, 1], [3, 3]]
    assert game.result.details["suns"] == [[0, 2]]


def test_marks_outside_the_grid_are_rejected(today, guest_id):
    with pytest.raises(InvalidCellError):
        services.save_marks(guest_id, today, [(0, 9)])


def test_each_guest_has_their_own_game(today):
    first, second = uuid.uuid4(), uuid.uuid4()
    services.place_sun(first, today, 0, 2)

    assert services.open_game(second, today).result.details == {}


def test_a_future_day_cannot_be_played(today, guest_id):
    with pytest.raises(NoPuzzleError):
        services.open_game(guest_id, today + timedelta(days=1))
