"""API views for the Logic game app."""

from datetime import date

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from apps.common.players import get_guest_id

from .. import services
from .serializers import (
    LogicGameSerializer,
    MarksInputSerializer,
    PlaceInputSerializer,
    PlaceResultSerializer,
)


@extend_schema(responses=LogicGameSerializer)
@api_view(["GET"])
def game(request: Request, day: date) -> Response:
    """The player's board for the day. Opening it the first time starts the clock."""
    logic_game = services.open_game(get_guest_id(request), day)
    return Response(LogicGameSerializer(logic_game).data)


@extend_schema(request=PlaceInputSerializer, responses=PlaceResultSerializer)
@api_view(["POST"])
def place(request: Request, day: date) -> Response:
    """Place a sun. The server says whether it is correct; the last correct sun ends the game."""
    data = PlaceInputSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    outcome = services.place_sun(
        get_guest_id(request), day, data.validated_data["row"], data.validated_data["col"]
    )
    return Response(PlaceResultSerializer(outcome).data)


@extend_schema(request=MarksInputSerializer, responses=LogicGameSerializer)
@api_view(["POST"])
def marks(request: Request, day: date) -> Response:
    """Save the player's X marks, so a refresh restores them."""
    data = MarksInputSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    cells = [(row, col) for row, col in data.validated_data["marks"]]
    logic_game = services.save_marks(get_guest_id(request), day, cells)
    return Response(LogicGameSerializer(logic_game).data)
