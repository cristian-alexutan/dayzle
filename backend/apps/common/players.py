"""Player identity. Games know a player only by the id returned by ``get_guest_id``."""

import uuid

from django.http import HttpRequest

GUEST_ID_SESSION_KEY = "guest_id"


def get_guest_id(request: HttpRequest) -> uuid.UUID:
    """Return the id games use for this player.

    A signed-in user always plays as their account's ``player_id``, the same in every session,
    so their results follow them across sign-outs and devices. Anyone else is an anonymous guest
    with an id stored in their session, created on first use.
    """
    user = getattr(request, "user", None)
    player_id = getattr(user, "player_id", None)
    if user is not None and user.is_authenticated and player_id is not None:
        return player_id
    value = request.session.get(GUEST_ID_SESSION_KEY)
    if value is None:
        value = str(uuid.uuid4())
        request.session[GUEST_ID_SESSION_KEY] = value
    return uuid.UUID(value)
