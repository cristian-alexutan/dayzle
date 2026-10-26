"""Anonymous player identity. Every visitor gets a guest id stored in their session."""

import uuid

from django.http import HttpRequest

GUEST_ID_SESSION_KEY = "guest_id"


def get_guest_id(request: HttpRequest) -> uuid.UUID:
    """Return the visitor's guest id, creating it on first use."""
    value = request.session.get(GUEST_ID_SESSION_KEY)
    if value is None:
        value = str(uuid.uuid4())
        request.session[GUEST_ID_SESSION_KEY] = value
    return uuid.UUID(value)
