"""API views for the Math game app."""

from datetime import date

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from apps.common.players import get_guest_id

from .. import services
from .serializers import MathGameSerializer, StepsInputSerializer, SubmitInputSerializer


@extend_schema(responses=MathGameSerializer)
@api_view(["GET"])
def game(request: Request, day: date) -> Response:
    """The player's board for the day. Opening it the first time starts the clock."""
    math_game = services.open_game(get_guest_id(request), day)
    return Response(MathGameSerializer(math_game).data)


@extend_schema(request=StepsInputSerializer, responses=MathGameSerializer)
@api_view(["POST"])
def progress(request: Request, day: date) -> Response:
    """Save the board after a step, undo or reset. The server replays every step."""
    data = StepsInputSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    math_game = services.save_steps(get_guest_id(request), day, data.to_steps())
    return Response(MathGameSerializer(math_game).data)


@extend_schema(request=SubmitInputSerializer, responses=MathGameSerializer)
@api_view(["POST"])
def submit(request: Request, day: date) -> Response:
    """Finish the game; the board comes back with the score and the example solution."""
    data = SubmitInputSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    math_game = services.submit(get_guest_id(request), day, data.to_steps())
    return Response(MathGameSerializer(math_game).data)
