"""API views for the Word game app."""

from datetime import date

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from apps.common.players import get_guest_id

from .. import services
from .serializers import GuessInputSerializer, WordGameSerializer


@extend_schema(responses=WordGameSerializer)
@api_view(["GET"])
def game(request: Request, day: date) -> Response:
    """The player's board for the day. Opening it the first time starts the clock."""
    word_game = services.open_game(get_guest_id(request), day)
    return Response(WordGameSerializer(word_game).data)


@extend_schema(request=GuessInputSerializer, responses=WordGameSerializer)
@api_view(["POST"])
def guess(request: Request, day: date) -> Response:
    """Send a guess; the board comes back with its colors (and the answer once finished)."""
    data = GuessInputSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    word_game = services.guess(get_guest_id(request), day, data.validated_data["guess"])
    return Response(WordGameSerializer(word_game).data)
