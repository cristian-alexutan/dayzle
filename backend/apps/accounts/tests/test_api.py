"""API tests for the accounts app."""

import pytest

from apps.accounts.exceptions import InvalidGoogleTokenError
from apps.accounts.services import GoogleProfile
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
    assert body["guest_id"] == guest_id
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
