import uuid
from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.puzzles.tests.factories import DailyPuzzleFactory
from apps.results import services
from apps.results.exceptions import AlreadyPlayedError
from apps.results.models import GameResult
from apps.results.selectors import get_result

from .factories import GameResultFactory

pytestmark = pytest.mark.django_db


def test_start_creates_an_in_progress_result_and_resume_returns_it():
    guest_id, puzzle = uuid.uuid4(), DailyPuzzleFactory()

    first = services.start_or_resume(guest_id, puzzle)
    again = services.start_or_resume(guest_id, puzzle)

    assert first.pk == again.pk
    assert first.status == GameResult.Status.IN_PROGRESS
    assert first.is_archive is False
    assert get_result(guest_id, puzzle) == first


def test_each_guest_gets_their_own_result():
    puzzle = DailyPuzzleFactory()

    first = services.start_or_resume(uuid.uuid4(), puzzle)
    second = services.start_or_resume(uuid.uuid4(), puzzle)

    assert first.pk != second.pk


def test_progress_is_saved_in_details():
    result = GameResultFactory()

    services.save_progress(result, {"guesses": ["CASĂ"]})

    result.refresh_from_db()
    assert result.details == {"guesses": ["CASĂ"]}


def test_complete_records_score_and_active_time_as_duration():
    result = GameResultFactory(
        active_ms=60_000, last_active_at=timezone.now() - timedelta(seconds=10)
    )

    done = services.complete(result, solved=True, score=300, details={"guesses": 3})

    assert done.status == GameResult.Status.COMPLETED
    assert done.solved is True
    assert done.score == 300
    assert done.details == {"guesses": 3}
    assert 70_000 <= done.duration_ms < 75_000


def test_activity_counts_the_time_since_the_last_activity():
    result = GameResultFactory(last_active_at=timezone.now() - timedelta(seconds=10))

    services.record_activity(result)

    result.refresh_from_db()
    assert 10_000 <= result.active_ms < 15_000


def test_time_away_from_the_game_counts_only_up_to_the_cap():
    # The player opened the game, left for hours and came back to finish it.
    result = GameResultFactory(
        started_at=timezone.now() - timedelta(hours=5),
        active_ms=20_000,
        last_active_at=timezone.now() - timedelta(hours=5),
    )

    done = services.complete(result, solved=True, score=100)

    cap_ms = int(services.ACTIVITY_GAP_CAP.total_seconds() * 1000)
    assert done.duration_ms == 20_000 + cap_ms


def test_saving_progress_counts_as_activity():
    result = GameResultFactory(last_active_at=timezone.now() - timedelta(seconds=5))

    services.save_progress(result, {"guesses": ["CASĂ"]})

    result.refresh_from_db()
    assert 5_000 <= result.active_ms < 10_000


def test_a_completed_puzzle_cannot_be_played_again():
    result = services.complete(GameResultFactory(), solved=False, score=0)

    with pytest.raises(AlreadyPlayedError):
        services.complete(result, solved=True, score=100)
    with pytest.raises(AlreadyPlayedError):
        services.save_progress(result, {})
    with pytest.raises(AlreadyPlayedError):
        services.record_activity(result)


def test_result_must_belong_to_a_player():
    with pytest.raises(IntegrityError):
        GameResultFactory(guest_id=None)
