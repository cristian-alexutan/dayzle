import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.common.players import GUEST_ID_SESSION_KEY
from apps.puzzles.tests.factories import DailyPuzzleFactory
from apps.results import services

from .factories import GameResultFactory

pytestmark = pytest.mark.django_db

HEARTBEAT_URL = "/api/v1/results/word/today/heartbeat/"


def play_as(api_client, guest_id):
    session = api_client.session
    session[GUEST_ID_SESSION_KEY] = str(guest_id)
    session.save()


def test_heartbeat_counts_active_time(api_client):
    guest_id = uuid.uuid4()
    play_as(api_client, guest_id)
    result = GameResultFactory(
        daily_puzzle=DailyPuzzleFactory(),
        guest_id=guest_id,
        last_active_at=timezone.now() - timedelta(seconds=10),
    )

    response = api_client.post(HEARTBEAT_URL)

    assert response.status_code == 204
    result.refresh_from_db()
    assert 10_000 <= result.active_ms < 15_000


def test_heartbeat_before_opening_the_game_is_rejected(api_client):
    DailyPuzzleFactory()

    response = api_client.post(HEARTBEAT_URL)

    assert response.status_code == 404
    assert response.data["error"]["code"] == "not_started"


def test_heartbeat_after_finishing_is_rejected(api_client):
    guest_id = uuid.uuid4()
    play_as(api_client, guest_id)
    result = GameResultFactory(daily_puzzle=DailyPuzzleFactory(), guest_id=guest_id)
    services.complete(result, solved=True, score=100)

    response = api_client.post(HEARTBEAT_URL)

    assert response.status_code == 409
    assert response.data["error"]["code"] == "already_played"


def test_heartbeat_without_a_puzzle_today_is_rejected(api_client):
    response = api_client.post(HEARTBEAT_URL)

    assert response.status_code == 404
    assert response.data["error"]["code"] == "no_puzzle"
