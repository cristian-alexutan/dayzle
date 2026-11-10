"""API serializers for the Logic game app."""

from rest_framework import serializers

from apps.results.models import GameResult

from ..services import CellContent


class CellInputSerializer(serializers.Serializer):
    row = serializers.IntegerField(min_value=0)
    col = serializers.IntegerField(min_value=0)
    content = serializers.ChoiceField(choices=[content.value for content in CellContent])


class LogicGameSerializer(serializers.Serializer):
    """The player's board. ``solved``, ``score`` and ``duration_ms`` stay null until the game
    ends. ``elapsed_ms`` is only for display. The solution is never sent."""

    date = serializers.DateField(source="puzzle.daily_puzzle.date")
    status = serializers.ChoiceField(choices=GameResult.Status.choices, source="result.status")
    size = serializers.IntegerField(source="puzzle.size")
    regions = serializers.ListField(
        child=serializers.ListField(child=serializers.IntegerField()), source="puzzle.regions"
    )
    suns = serializers.SerializerMethodField()
    marks = serializers.SerializerMethodField()
    mistakes = serializers.SerializerMethodField()
    solved = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    duration_ms = serializers.SerializerMethodField()
    elapsed_ms = serializers.SerializerMethodField()

    def _finished(self, game) -> bool:
        return game.result.status == GameResult.Status.COMPLETED

    def get_suns(self, game) -> list[list[int]]:
        return game.result.details.get("suns", [])

    def get_marks(self, game) -> list[list[int]]:
        return game.result.details.get("marks", [])

    def get_mistakes(self, game) -> int:
        return game.result.details.get("mistakes", 0)

    def get_solved(self, game) -> bool | None:
        return game.result.solved if self._finished(game) else None

    def get_score(self, game) -> int | None:
        return game.result.score if self._finished(game) else None

    def get_duration_ms(self, game) -> int | None:
        return game.result.duration_ms if self._finished(game) else None

    def get_elapsed_ms(self, game) -> int:
        """Active play time so far, so the on-screen timer continues after a refresh."""
        if self._finished(game) and game.result.duration_ms is not None:
            return game.result.duration_ms
        return game.result.active_ms


class CellResultSerializer(serializers.Serializer):
    """Whether a new sun was rejected, the suns it conflicts with, and the updated board."""

    rejected = serializers.BooleanField()
    conflicts = serializers.ListField(child=serializers.ListField(child=serializers.IntegerField()))
    game = LogicGameSerializer()
