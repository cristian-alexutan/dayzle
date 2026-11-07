"""Write operations and business rules for the accounts app."""

import json
import uuid
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.db import transaction
from django.http import HttpRequest

from apps.common.players import GUEST_ID_SESSION_KEY, get_guest_id
from apps.results.models import GameResult

from .exceptions import GoogleAuthNotConfiguredError, InvalidGoogleTokenError
from .models import User
from .selectors import SessionState, get_session_state

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
VALID_GOOGLE_ISSUERS = frozenset({"accounts.google.com", "https://accounts.google.com"})


@dataclass(frozen=True)
class GoogleProfile:
    sub: str
    email: str
    first_name: str = ""
    last_name: str = ""


def verify_google_id_token(id_token: str) -> GoogleProfile:
    """Verify a Google ID token and return the user's Google profile."""
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        raise GoogleAuthNotConfiguredError()

    url = f"{GOOGLE_TOKENINFO_URL}?{urlencode({'id_token': id_token})}"
    try:
        with urlopen(url, timeout=5) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise InvalidGoogleTokenError() from exc

    if payload.get("aud") != client_id:
        raise InvalidGoogleTokenError()

    if payload.get("iss") not in VALID_GOOGLE_ISSUERS:
        raise InvalidGoogleTokenError()

    email_verified = payload.get("email_verified")
    if email_verified not in (True, "true", "True"):
        raise InvalidGoogleTokenError()

    email = (payload.get("email") or "").strip().lower()
    sub = (payload.get("sub") or "").strip()
    if not email or not sub:
        raise InvalidGoogleTokenError()

    return GoogleProfile(
        sub=sub,
        email=email,
        first_name=(payload.get("given_name") or "").strip()[:150],
        last_name=(payload.get("family_name") or "").strip()[:150],
    )


def _unique_username(base: str) -> str:
    candidate = (base or "player")[:140]
    if not User.objects.filter(username=candidate).exists():
        return candidate
    suffix = 1
    while True:
        numbered = f"{candidate}_{suffix}"
        if not User.objects.filter(username=numbered).exists():
            return numbered
        suffix += 1


@transaction.atomic
def get_or_create_google_user(profile: GoogleProfile) -> User:
    """Find or create the user corresponding to a verified Google profile."""
    user = User.objects.filter(email__iexact=profile.email).first()
    if user is None:
        local_part = profile.email.split("@", 1)[0]
        user = User(
            username=_unique_username(local_part),
            email=profile.email,
            first_name=profile.first_name,
            last_name=profile.last_name,
        )
        user.set_unusable_password()
        user.save()
        return user

    updated_fields: list[str] = []
    if profile.first_name and not user.first_name:
        user.first_name = profile.first_name
        updated_fields.append("first_name")
    if profile.last_name and not user.last_name:
        user.last_name = profile.last_name
        updated_fields.append("last_name")
    if updated_fields:
        user.save(update_fields=updated_fields)
    return user


@transaction.atomic
def claim_guest_results(guest_id: uuid.UUID, user: User) -> int:
    """Attach any anonymous GameResults from this session's guest_id to the user.

    Keeps ``guest_id`` populated on the row so games that look up results by ``guest_id``
    continue to see the player's progress seamlessly. If the user already has a result for the
    same daily puzzle from another session, that row is left untouched.
    """
    existing_puzzle_ids = set(
        GameResult.objects.filter(user=user).values_list("daily_puzzle_id", flat=True)
    )
    return (
        GameResult.objects.filter(guest_id=guest_id, user__isnull=True)
        .exclude(daily_puzzle_id__in=existing_puzzle_ids)
        .update(user=user)
    )


def sign_in_with_google(request: HttpRequest, id_token: str) -> SessionState:
    """Verify a Google ID token, sign the user into the session, and claim guest results."""
    guest_id = get_guest_id(request)
    profile = verify_google_id_token(id_token)
    user = get_or_create_google_user(profile)
    claim_guest_results(guest_id, user)
    auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    request.session[GUEST_ID_SESSION_KEY] = str(guest_id)
    return get_session_state(request)


def sign_out(request: HttpRequest) -> SessionState:
    """Sign the user out and assign a fresh guest identity for the session."""
    auth_logout(request)
    get_guest_id(request)
    return get_session_state(request)
