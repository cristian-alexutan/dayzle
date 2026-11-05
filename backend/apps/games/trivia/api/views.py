"""API views for the Trivia game app."""

from datetime import date

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from apps.common.players import get_guest_id

from .. import services
from .serializers import AnswerInputSerializer, TriviaGameSerializer


@extend_schema(responses=TriviaGameSerializer)
@api_view(["GET"])
def game(request: Request, day: date) -> Response:
    """The day's 5 questions and the player's answers so far. The first open starts the clock."""
    trivia_game = services.open_game(get_guest_id(request), day)
    return Response(TriviaGameSerializer(trivia_game).data)


@extend_schema(request=AnswerInputSerializer, responses=TriviaGameSerializer)
@api_view(["POST"])
def answer(request: Request, day: date) -> Response:
    """Answer the next question; the quiz comes back with that question's correct choice."""
    data = AnswerInputSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    trivia_game = services.answer(
        get_guest_id(request),
        day,
        data.validated_data["question"],
        data.validated_data["choice"],
    )
    return Response(TriviaGameSerializer(trivia_game).data)
