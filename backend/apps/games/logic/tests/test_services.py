import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.common.time import today_in_romania
from apps.games.logic import rules, services
from apps.games.logic.exceptions import InvalidCellError
from apps.games.logic.services import CellContent
from apps.puzzles.exceptions import NoPuzzleError
from apps.results.exceptions import AlreadyPlayedError
from apps.results.models import GameResult

from .factories import LogicPuzzleFactory

pytestmark = pytest.mark.django_db

# The demo level's solution, as cells: (0, 2), (1, 0), (2, 4), (3, 1), (4, 3), (5, 5).
SOLUTION_CELLS = list(enumerate(rules.DEMO_SOLUTION))
SUN, MARK, EMPTY = CellContent.SUN, CellContent.MARK, CellContent.EMPTY


@pytest.fixture
def today():
    LogicPuzzleFactory()
    return today_in_romania()


@pytest.fixture
def guest_id():
    return uuid.uuid4()


def set_cell(guest_id, day, cell, content):
    return services.set_cell(guest_id, day, cell[0], cell[1], content)


def place_all(guest_id, day, cells=SOLUTION_CELLS):
    outcome = None
    for cell in cells:
        outcome = set_cell(guest_id, day, cell, SUN)
    return outcome


def details(outcome):
    return outcome.game.result.details


def test_opening_the_game_starts_it_with_an_empty_board(today, guest_id):
    game = services.open_game(guest_id, today)

    assert game.result.status == GameResult.Status.IN_PROGRESS
    assert game.result.details == {}


def test_a_sun_that_breaks_no_rule_is_kept(today, guest_id):
    outcome = set_cell(guest_id, today, (0, 2), SUN)

    assert outcome.rejected is False
    assert details(outcome) == {"suns": [[0, 2]], "marks": [], "mistakes": 0}


def test_suns_are_not_checked_against_the_solution(today, guest_id):
    # (0, 0) is not in the solution, but nothing on the board conflicts with it yet.
    outcome = set_cell(guest_id, today, (0, 0), SUN)

    assert outcome.rejected is False
    assert details(outcome)["suns"] == [[0, 0]]


def test_a_sun_that_breaks_a_rule_is_rejected_as_a_mistake(today, guest_id):
    set_cell(guest_id, today, (0, 2), SUN)

    # (0, 3) is on the same row and in the same region as the sun on (0, 2).
    outcome = set_cell(guest_id, today, (0, 3), SUN)

    assert outcome.rejected is True
    assert outcome.conflicts == [(0, 2)]
    assert details(outcome)["suns"] == [[0, 2]]
    assert details(outcome)["mistakes"] == 1


def test_a_rejected_sun_leaves_its_x_in_place(today, guest_id):
    set_cell(guest_id, today, (0, 2), SUN)
    set_cell(guest_id, today, (1, 1), MARK)

    # (1, 1) touches the sun on (0, 2) diagonally.
    outcome = set_cell(guest_id, today, (1, 1), SUN)

    assert outcome.rejected is True
    assert details(outcome)["marks"] == [[1, 1]]


def test_an_accepted_sun_replaces_the_x_of_its_cell(today, guest_id):
    set_cell(guest_id, today, (0, 2), MARK)
    set_cell(guest_id, today, (5, 0), MARK)

    outcome = set_cell(guest_id, today, (0, 2), SUN)

    assert details(outcome)["suns"] == [[0, 2]]
    assert details(outcome)["marks"] == [[5, 0]]


def test_a_sun_can_be_removed_without_a_mistake(today, guest_id):
    set_cell(guest_id, today, (0, 0), SUN)

    outcome = set_cell(guest_id, today, (0, 0), EMPTY)

    assert details(outcome) == {"suns": [], "marks": [], "mistakes": 0}


def test_a_sun_can_be_turned_into_an_x(today, guest_id):
    set_cell(guest_id, today, (0, 0), SUN)

    outcome = set_cell(guest_id, today, (0, 0), MARK)

    assert details(outcome)["suns"] == []
    assert details(outcome)["marks"] == [[0, 0]]


def test_setting_the_same_content_twice_changes_nothing(today, guest_id):
    set_cell(guest_id, today, (0, 2), SUN)
    set_cell(guest_id, today, (1, 1), MARK)

    sun_again = set_cell(guest_id, today, (0, 2), SUN)
    mark_again = set_cell(guest_id, today, (1, 1), MARK)

    assert sun_again.rejected is False
    assert details(mark_again) == {"suns": [[0, 2]], "marks": [[1, 1]], "mistakes": 0}


def test_a_cell_outside_the_grid_is_rejected_and_not_counted(today, guest_id):
    with pytest.raises(InvalidCellError):
        set_cell(guest_id, today, (6, 0), SUN)

    assert services.open_game(guest_id, today).result.details == {}


def test_the_last_sun_finishes_the_game_with_a_score(today, guest_id):
    outcome = place_all(guest_id, today)

    result = outcome.game.result
    assert result.status == GameResult.Status.COMPLETED
    assert result.solved is True
    assert result.score == rules.score(6, result.duration_ms, mistakes=0)


def test_the_score_uses_the_measured_duration_and_the_mistakes(today, guest_id):
    set_cell(guest_id, today, (0, 2), SUN)
    set_cell(guest_id, today, (0, 3), SUN)  # rejected: a mistake
    # Pretend the player has already played for 3 minutes.
    result = GameResult.objects.get(guest_id=guest_id)
    result.active_ms = 3 * 60_000
    result.last_active_at = timezone.now()
    result.save()

    outcome = place_all(guest_id, today, SOLUTION_CELLS[1:])

    result = outcome.game.result
    assert 3 * 60_000 <= result.duration_ms < 3 * 60_000 + 5_000
    assert result.details["mistakes"] == 1
    assert result.score == rules.score(6, result.duration_ms, mistakes=1)
    assert 695 <= result.score <= 700


def test_clearing_the_board_keeps_the_mistakes(today, guest_id):
    set_cell(guest_id, today, (0, 2), SUN)
    set_cell(guest_id, today, (0, 3), SUN)  # rejected: a mistake
    set_cell(guest_id, today, (5, 0), MARK)

    game = services.clear_board(guest_id, today)

    assert game.result.details == {"suns": [], "marks": [], "mistakes": 1}


def test_playing_after_finishing_is_already_played(today, guest_id):
    place_all(guest_id, today)

    with pytest.raises(AlreadyPlayedError):
        set_cell(guest_id, today, (0, 0), MARK)
    with pytest.raises(AlreadyPlayedError):
        services.clear_board(guest_id, today)


def test_each_guest_has_their_own_game(today):
    first, second = uuid.uuid4(), uuid.uuid4()
    set_cell(first, today, (0, 2), SUN)

    assert services.open_game(second, today).result.details == {}


def test_a_future_day_cannot_be_played(today, guest_id):
    with pytest.raises(NoPuzzleError):
        services.open_game(guest_id, today + timedelta(days=1))
