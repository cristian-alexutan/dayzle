"""Read queries for the accounts app."""

import uuid
from dataclasses import dataclass

from django.http import HttpRequest

from apps.common.players import get_guest_id

from .models import User


@dataclass(frozen=True)
class SessionState:
    guest_id: uuid.UUID
    user: User | None

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None


def get_session_state(request: HttpRequest) -> SessionState:
    """Return the current visitor's guest id and authenticated user (if signed in)."""
    guest_id = get_guest_id(request)
    user = (
        request.user if isinstance(request.user, User) and request.user.is_authenticated else None
    )
    return SessionState(guest_id=guest_id, user=user)
