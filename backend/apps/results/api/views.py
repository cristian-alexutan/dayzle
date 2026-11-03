"""API views for the results app."""

from datetime import date

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from apps.common.players import get_guest_id

from .. import services


@extend_schema(request=None, responses={204: None})
@api_view(["POST"])
def heartbeat(request: Request, game: str, day: date) -> Response:
    """Count the player as active. The frontend calls this every 15 s while the game is visible."""
    services.heartbeat(get_guest_id(request), game, day)
    return Response(status=status.HTTP_204_NO_CONTENT)
