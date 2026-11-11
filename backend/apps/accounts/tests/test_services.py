"""Unit tests for the accounts app services."""

import io
import json
from urllib.error import URLError

import pytest

from apps.accounts.exceptions import GoogleAuthNotConfiguredError, InvalidGoogleTokenError
from apps.accounts.models import User
from apps.accounts.services import (
    GoogleProfile,
    claim_guest_results,
    get_or_create_google_user,
    verify_google_id_token,
)
from apps.puzzles.tests.factories import DailyPuzzleFactory
from apps.results.models import GameResult
from apps.results.tests.factories import GameResultFactory

pytestmark = pytest.mark.django_db


def _mock_urlopen(monkeypatch: pytest.MonkeyPatch, payload: dict) -> None:
    raw = json.dumps(payload).encode("utf-8")

    class _DummyResponse(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    monkeypatch.setattr(
        "apps.accounts.services.urlopen",
        lambda url, timeout=5: _DummyResponse(raw),
    )


def test_verify_google_id_token_requires_configured_client_id(settings):
    settings.GOOGLE_CLIENT_ID = ""
    with pytest.raises(GoogleAuthNotConfiguredError):
        verify_google_id_token("token-123")


def test_verify_google_id_token_returns_profile_for_valid_token(settings, monkeypatch):
    settings.GOOGLE_CLIENT_ID = "my-client.apps.googleusercontent.com"
    _mock_urlopen(
        monkeypatch,
        {
            "aud": "my-client.apps.googleusercontent.com",
            "iss": "https://accounts.google.com",
            "email_verified": "true",
            "sub": "google-sub-1",
            "email": "Andrei.Maxim@Example.com",
            "given_name": "Andrei",
            "family_name": "Maxim",
        },
    )

    profile = verify_google_id_token("valid-token")

    assert profile == GoogleProfile(
        sub="google-sub-1",
        email="andrei.maxim@example.com",
        first_name="Andrei",
        last_name="Maxim",
    )


@pytest.mark.parametrize(
    "override",
    [
        {"aud": "other-client.apps.googleusercontent.com"},
        {"iss": "https://evil.example.com"},
        {"email_verified": "false"},
        {"email": ""},
        {"sub": ""},
    ],
)
def test_verify_google_id_token_rejects_invalid_claims(settings, monkeypatch, override):
    settings.GOOGLE_CLIENT_ID = "my-client.apps.googleusercontent.com"
    base = {
        "aud": "my-client.apps.googleusercontent.com",
        "iss": "accounts.google.com",
        "email_verified": "true",
        "sub": "google-sub-1",
        "email": "user@example.com",
    }
    _mock_urlopen(monkeypatch, {**base, **override})

    with pytest.raises(InvalidGoogleTokenError):
        verify_google_id_token("bad-token")


def test_verify_google_id_token_handles_network_errors(settings, monkeypatch):
    settings.GOOGLE_CLIENT_ID = "my-client.apps.googleusercontent.com"

    def _raise_url_error(url, timeout=5):
        raise URLError("unreachable")

    monkeypatch.setattr("apps.accounts.services.urlopen", _raise_url_error)

    with pytest.raises(InvalidGoogleTokenError):
        verify_google_id_token("bad-token")


def test_get_or_create_google_user_creates_and_reuses_user():
    profile = GoogleProfile(
        sub="sub-1",
        email="andrei@example.com",
        first_name="Andrei",
        last_name="Maxim",
    )

    created = get_or_create_google_user(profile)
    assert created.email == "andrei@example.com"
    assert created.username == "andrei"
    assert created.first_name == "Andrei"
    assert created.last_name == "Maxim"
    assert not created.has_usable_password()

    reused = get_or_create_google_user(profile)
    assert reused.pk == created.pk
    assert User.objects.count() == 1


def test_get_or_create_google_user_disambiguates_colliding_usernames():
    User.objects.create_user(username="andrei", email="other@example.com")
    profile = GoogleProfile(sub="sub-2", email="andrei@second.com")

    user = get_or_create_google_user(profile)
    assert user.username == "andrei_1"


def test_claim_guest_results_moves_guest_results_onto_the_account():
    user = User.objects.create_user(username="andrei", email="andrei@example.com")
    puzzle_1 = DailyPuzzleFactory(game="word")
    puzzle_2 = DailyPuzzleFactory(game="math")

    guest_result_1 = GameResultFactory(daily_puzzle=puzzle_1, user=None)
    guest_id = guest_result_1.guest_id
    guest_result_2 = GameResultFactory(daily_puzzle=puzzle_2, guest_id=guest_id, user=None)
    # The account already played puzzle_2, signed in on another device.
    GameResultFactory(daily_puzzle=puzzle_2, guest_id=user.player_id, user=user)

    claimed = claim_guest_results(guest_id, user)

    assert claimed == 1
    guest_result_1.refresh_from_db()
    guest_result_2.refresh_from_db()
    assert (guest_result_1.user, guest_result_1.guest_id) == (user, user.player_id)
    assert (guest_result_2.user, guest_result_2.guest_id) == (None, guest_id)
    assert GameResult.objects.filter(user=user).count() == 2


def test_claim_guest_results_skips_puzzles_played_signed_in_but_not_yet_linked():
    user = User.objects.create_user(username="andrei", email="andrei@example.com")
    puzzle = DailyPuzzleFactory(game="word")
    played_signed_in = GameResultFactory(daily_puzzle=puzzle, guest_id=user.player_id, user=None)
    guest_result = GameResultFactory(daily_puzzle=puzzle, user=None)

    claimed = claim_guest_results(guest_result.guest_id, user)

    assert claimed == 0
    played_signed_in.refresh_from_db()
    guest_result.refresh_from_db()
    assert played_signed_in.user == user
    assert guest_result.user is None
