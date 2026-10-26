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


def test_complete_records_score_and_server_measured_duration():
    result = GameResultFactory(started_at=timezone.now() - timedelta(seconds=90))

    done = services.complete(result, solved=True, score=300, details={"guesses": 3})

    assert done.status == GameResult.Status.COMPLETED
    assert done.solved is True
    assert done.score == 300
    assert done.details == {"guesses": 3}
    assert 90_000 <= done.duration_ms < 95_000


def test_a_completed_puzzle_cannot_be_played_again():
    result = services.complete(GameResultFactory(), solved=False, score=0)

    with pytest.raises(AlreadyPlayedError):
        services.complete(result, solved=True, score=100)
    with pytest.raises(AlreadyPlayedError):
        services.save_progress(result, {})


def test_result_must_belong_to_a_player():
    with pytest.raises(IntegrityError):
        GameResultFactory(guest_id=None)
