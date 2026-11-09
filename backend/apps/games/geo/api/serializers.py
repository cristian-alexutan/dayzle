"""API serializers for the GeoGuesser game app."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.results.models import GameResult

from .. import rules


class RegionQuerySerializer(serializers.Serializer):
    region = serializers.SlugField(
        required=False, help_text="The region's key. Defaults to the default region."
    )


class GeoGuessInputSerializer(serializers.Serializer):
    round = serializers.IntegerField(min_value=1, max_value=rules.ROUNDS)
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lng = serializers.FloatField(min_value=-180, max_value=180)


class BoundsSerializer(serializers.Serializer):
    south = serializers.FloatField()
    west = serializers.FloatField()
    north = serializers.FloatField()
    east = serializers.FloatField()


class RegionSerializer(serializers.Serializer):
    """A region the player can choose. Its bounds limit the guess map; they aren't secret."""

    key = serializers.CharField()
    name = serializers.CharField()
    bounds = BoundsSerializer()


class PointSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lng = serializers.FloatField()


class RoundResultSerializer(serializers.Serializer):
    """A guessed round: the player's point and, now that it's guessed, the real one."""

    round = serializers.IntegerField()
    guess = PointSerializer()
    location = PointSerializer()
    distance_m = serializers.IntegerField()
    score = serializers.IntegerField()


class GeoGameSerializer(serializers.Serializer):
    """The player's game. Only the current round's panorama is sent, never its coordinates.

    A location's coordinates appear only in ``results``, after its round is guessed. ``solved``
    and ``duration_ms`` stay null until the fifth guess.
    """

    date = serializers.DateField(source="puzzle.daily_puzzle.date")
    region = RegionSerializer(source="puzzle.region")
    status = serializers.ChoiceField(choices=GameResult.Status.choices, source="result.status")
    rounds = serializers.SerializerMethodField()
    current_round = serializers.SerializerMethodField()
    panorama_id = serializers.SerializerMethodField()
    results = serializers.SerializerMethodField()
    total_score = serializers.SerializerMethodField()
    max_score = serializers.SerializerMethodField()
    solved = serializers.SerializerMethodField()
    duration_ms = serializers.SerializerMethodField()

    def _guesses(self, game) -> list[dict]:
        return game.result.details.get("guesses", [])

    def _finished(self, game) -> bool:
        return game.result.status == GameResult.Status.COMPLETED

    def get_rounds(self, game) -> int:
        return len(game.locations)

    def get_current_round(self, game) -> int | None:
        return None if self._finished(game) else len(self._guesses(game)) + 1

    def get_panorama_id(self, game) -> str | None:
        if self._finished(game):
            return None
        return game.locations[len(self._guesses(game))].panorama_id

    @extend_schema_field(RoundResultSerializer(many=True))
    def get_results(self, game) -> list[dict]:
        rows = []
        for given in self._guesses(game):
            location = game.locations[given["round"] - 1]
            rows.append(
                {
                    "round": given["round"],
                    "guess": {"lat": given["lat"], "lng": given["lng"]},
                    "location": {"lat": location.latitude, "lng": location.longitude},
                    "distance_m": given["distance_m"],
                    "score": given["score"],
                }
            )
        return RoundResultSerializer(rows, many=True).data

    def get_total_score(self, game) -> int:
        return rules.total_score(given["score"] for given in self._guesses(game))

    def get_max_score(self, game) -> int:
        return rules.MAX_SCORE

    def get_solved(self, game) -> bool | None:
        return game.result.solved if self._finished(game) else None

    def get_duration_ms(self, game) -> int | None:
        return game.result.duration_ms if self._finished(game) else None
