"""API serializers for the Logic game app."""

from rest_framework import serializers

from apps.results.models import GameResult

from .. import rules


class PlaceInputSerializer(serializers.Serializer):
    row = serializers.IntegerField(min_value=0)
    col = serializers.IntegerField(min_value=0)


class MarksInputSerializer(serializers.Serializer):
    # Each mark is a cell, sent as [row, col]. No valid request has more marks than the largest
    # grid has cells.
    marks = serializers.ListField(
        child=serializers.ListField(
            child=serializers.IntegerField(min_value=0), min_length=2, max_length=2
        ),
        max_length=rules.MAX_SIZE**2,
    )


class LogicGameSerializer(serializers.Serializer):
    """The player's board. The solution is never included; ``solved``, ``score`` and
    ``duration_ms`` stay null until the game ends."""

    date = serializers.DateField(source="puzzle.daily_puzzle.date")
    status = serializers.ChoiceField(choices=GameResult.Status.choices, source="result.status")
    size = serializers.IntegerField(source="puzzle.size")
    regions = serializers.ListField(
        child=serializers.ListField(child=serializers.IntegerField()), source="puzzle.regions"
    )
    suns = serializers.SerializerMethodField()
    marks = serializers.SerializerMethodField()
    mistakes = serializers.SerializerMethodField()
    streak = serializers.SerializerMethodField()
    solved = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    duration_ms = serializers.SerializerMethodField()

    def _finished(self, game) -> bool:
        return game.result.status == GameResult.Status.COMPLETED

    @staticmethod
    def _moves(game) -> list[bool]:
        return game.result.details.get("moves", [])

    def get_suns(self, game) -> list[list[int]]:
        return game.result.details.get("suns", [])

    def get_marks(self, game) -> list[list[int]]:
        return game.result.details.get("marks", [])

    def get_mistakes(self, game) -> int:
        return self._moves(game).count(False)

    def get_streak(self, game) -> int:
        return rules.current_streak(self._moves(game))

    def get_solved(self, game) -> bool | None:
        return game.result.solved if self._finished(game) else None

    def get_score(self, game) -> int | None:
        return game.result.score if self._finished(game) else None

    def get_duration_ms(self, game) -> int | None:
        return game.result.duration_ms if self._finished(game) else None


class PlaceResultSerializer(serializers.Serializer):
    """Whether the sun was correct, the suns it conflicts with, and the updated board."""

    correct = serializers.BooleanField()
    conflicts = serializers.ListField(child=serializers.ListField(child=serializers.IntegerField()))
    game = LogicGameSerializer()
