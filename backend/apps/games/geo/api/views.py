"""API views for the GeoGuesser game app."""

from datetime import date

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from apps.common.players import get_guest_id

from .. import services
from ..selectors import active_regions
from .serializers import (
    GeoGameSerializer,
    GeoGuessInputSerializer,
    RegionQuerySerializer,
    RegionSerializer,
)


def _region_key(request: Request) -> str | None:
    query = RegionQuerySerializer(data=request.query_params)
    query.is_valid(raise_exception=True)
    return query.validated_data.get("region")


@extend_schema(responses=RegionSerializer(many=True))
@api_view(["GET"])
def regions(request: Request) -> Response:
    """The regions a player can choose, the default one first."""
    return Response(RegionSerializer(active_regions(), many=True).data)


@extend_schema(parameters=[RegionQuerySerializer], responses=GeoGameSerializer)
@api_view(["GET"])
def game(request: Request, day: date) -> Response:
    """The current round's panorama and the guessed rounds. The first open starts the clock."""
    geo_game = services.open_game(get_guest_id(request), _region_key(request), day)
    return Response(GeoGameSerializer(geo_game).data)


@extend_schema(
    parameters=[RegionQuerySerializer], request=GeoGuessInputSerializer, responses=GeoGameSerializer
)
@api_view(["POST"])
def guess(request: Request, day: date) -> Response:
    """Guess the current round; the game comes back with its location and the next panorama."""
    region_key = _region_key(request)
    data = GeoGuessInputSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    geo_game = services.guess(
        get_guest_id(request),
        region_key,
        day,
        data.validated_data["round"],
        data.validated_data["lat"],
        data.validated_data["lng"],
    )
    return Response(GeoGameSerializer(geo_game).data)
