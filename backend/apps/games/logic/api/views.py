"""API views for the Logic game app."""

from datetime import date

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from apps.common.players import get_guest_id

from .. import services
from .serializers import CellInputSerializer, CellResultSerializer, LogicGameSerializer


@extend_schema(responses=LogicGameSerializer)
@api_view(["GET"])
def game(request: Request, day: date) -> Response:
    """The player's board for the day. Opening it the first time starts the clock."""
    logic_game = services.open_game(get_guest_id(request), day)
    return Response(LogicGameSerializer(logic_game).data)


@extend_schema(request=CellInputSerializer, responses=CellResultSerializer)
@api_view(["POST"])
def cell(request: Request, day: date) -> Response:
    """Set a cell to empty, an X or a sun. A sun that breaks a rule is rejected as a mistake;
    the last sun ends the game."""
    data = CellInputSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    outcome = services.set_cell(
        get_guest_id(request),
        day,
        data.validated_data["row"],
        data.validated_data["col"],
        services.CellContent(data.validated_data["content"]),
    )
    return Response(CellResultSerializer(outcome).data)


@extend_schema(request=None, responses=LogicGameSerializer)
@api_view(["POST"])
def clear(request: Request, day: date) -> Response:
    """Remove every sun and X from the board. Mistakes and time are kept."""
    logic_game = services.clear_board(get_guest_id(request), day)
    return Response(LogicGameSerializer(logic_game).data)
