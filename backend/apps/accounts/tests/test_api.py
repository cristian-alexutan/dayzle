"""API tests for the accounts app."""

import pytest
from rest_framework.test import APIClient

from apps.accounts.exceptions import InvalidGoogleTokenError
from apps.accounts.models import User
from apps.accounts.services import GoogleProfile
from apps.games.word.tests.factories import WordFactory, WordPuzzleFactory
from apps.results.tests.factories import GameResultFactory

pytestmark = pytest.mark.django_db


def test_me_returns_anonymous_guest_state(api_client):
    response = api_client.get("/api/v1/accounts/me/")

    assert response.status_code == 200
    body = response.json()
    assert body["is_authenticated"] is False
    assert body["guest_id"] is not None
    assert body["user"] is None


def test_google_login_signs_in_and_claims_guest_results(api_client, monkeypatch):
    me_before = api_client.get("/api/v1/accounts/me/").json()
    guest_id = me_before["guest_id"]
    result = GameResultFactory(guest_id=guest_id, user=None)

    monkeypatch.setattr(
        "apps.accounts.services.verify_google_id_token",
        lambda token: GoogleProfile(
            sub="sub-123",
            email="andrei@example.com",
            first_name="Andrei",
            last_name="Maxim",
        ),
    )

    response = api_client.post(
        "/api/v1/accounts/google/",
        {"credential": "valid-google-jwt"},
        format="json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_authenticated"] is True
    # Signed in, the player is the account's player_id, the same in every session.
    user = User.objects.get(email="andrei@example.com")
    assert body["guest_id"] == str(user.player_id)
    assert body["user"] == {
        "id": body["user"]["id"],
        "username": "andrei",
        "email": "andrei@example.com",
        "first_name": "Andrei",
        "last_name": "Maxim",
        "display_name": "Andrei Maxim",
    }

    result.refresh_from_db()
    assert result.user_id == body["user"]["id"]
    assert result.guest_id == user.player_id

    me_after = api_client.get("/api/v1/accounts/me/").json()
    assert me_after["is_authenticated"] is True
    assert me_after["user"]["email"] == "andrei@example.com"


def test_google_login_returns_401_on_invalid_token(api_client, monkeypatch):
    def _reject(token: str):
        raise InvalidGoogleTokenError()

    monkeypatch.setattr("apps.accounts.services.verify_google_id_token", _reject)

    response = api_client.post(
        "/api/v1/accounts/google/",
        {"credential": "invalid-jwt"},
        format="json",
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_google_token"


def test_logout_clears_authenticated_user_and_rotates_guest_id(api_client, monkeypatch):
    monkeypatch.setattr(
        "apps.accounts.services.verify_google_id_token",
        lambda token: GoogleProfile(sub="sub-123", email="andrei@example.com"),
    )
    signed_in = api_client.post(
        "/api/v1/accounts/google/",
        {"credential": "valid-google-jwt"},
        format="json",
    ).json()

    logged_out = api_client.post("/api/v1/accounts/logout/").json()

    assert logged_out["is_authenticated"] is False
    assert logged_out["user"] is None
    assert logged_out["guest_id"] != signed_in["guest_id"]


def _sign_in(api_client, monkeypatch, email="andrei@example.com"):
    monkeypatch.setattr(
        "apps.accounts.services.verify_google_id_token",
        lambda token: GoogleProfile(sub=f"sub-{email}", email=email),
    )
    response = api_client.post(
        "/api/v1/accounts/google/", {"credential": "valid-google-jwt"}, format="json"
    )
    assert response.status_code == 200


WORD_URL = "/api/v1/games/word/today/"


@pytest.fixture
def todays_word():
    WordPuzzleFactory(answer=WordFactory(text="carte"))


@pytest.mark.usefixtures("todays_word")
def test_a_game_finished_on_an_account_stays_finished_after_signing_out_and_in(
    api_client, monkeypatch
):
    _sign_in(api_client, monkeypatch)
    finished = api_client.post(f"{WORD_URL}guess/", {"guess": "carte"}, format="json")
    assert finished.data["status"] == "completed"

    api_client.post("/api/v1/accounts/logout/")
    _sign_in(api_client, monkeypatch)

    assert api_client.get(WORD_URL).data["status"] == "completed"
    again = api_client.post(f"{WORD_URL}guess/", {"guess": "carte"}, format="json")
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "already_played"


@pytest.mark.usefixtures("todays_word")
def test_a_game_finished_on_an_account_is_finished_on_another_device(api_client, monkeypatch):
    _sign_in(api_client, monkeypatch)
    api_client.post(f"{WORD_URL}guess/", {"guess": "carte"}, format="json")

    other_device = APIClient()
    _sign_in(other_device, monkeypatch)

    assert other_device.get(WORD_URL).data["status"] == "completed"


@pytest.mark.usefixtures("todays_word")
def test_signing_out_does_not_show_the_account_game_to_the_guest(api_client, monkeypatch):
    _sign_in(api_client, monkeypatch)
    api_client.post(f"{WORD_URL}guess/", {"guess": "carte"}, format="json")

    api_client.post("/api/v1/accounts/logout/")

    assert api_client.get(WORD_URL).data["status"] == "in_progress"


@pytest.mark.usefixtures("todays_word")
def test_a_guest_game_on_a_puzzle_the_account_finished_is_not_claimed(api_client, monkeypatch):
    _sign_in(api_client, monkeypatch)
    api_client.post(f"{WORD_URL}guess/", {"guess": "carte"}, format="json")
    api_client.post("/api/v1/accounts/logout/")
    # Played again as a guest after signing out: signing back in keeps the account's game.
    api_client.get(WORD_URL)

    _sign_in(api_client, monkeypatch)

    assert api_client.get(WORD_URL).data["status"] == "completed"
