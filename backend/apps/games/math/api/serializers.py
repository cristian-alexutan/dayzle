"""API serializers for the Math game app."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.results.models import GameResult

from .. import rules
from ..models import DIFFICULTY_CHOICES

OPERATORS = [operator.value for operator in rules.Operator]
# Keeps requests small; the rules themselves reject more than rules.MAX_STEPS steps.
MAX_REQUEST_STEPS = 10


class StepInputSerializer(serializers.Serializer):
    left = serializers.IntegerField()
    op = serializers.ChoiceField(choices=OPERATORS)
    right = serializers.IntegerField()


class StepsInputSerializer(serializers.Serializer):
    """The whole board's steps, from the start. Anything the browser computed is ignored."""

    steps = StepInputSerializer(many=True, max_length=MAX_REQUEST_STEPS)

    def to_steps(self) -> list[rules.Step]:
        return [
            rules.Step(step["left"], rules.Operator(step["op"]), step["right"])
            for step in self.validated_data["steps"]
        ]


class SubmitInputSerializer(StepsInputSerializer):
    steps = StepInputSerializer(many=True, min_length=1, max_length=MAX_REQUEST_STEPS)


class PlayedStepSerializer(serializers.Serializer):
    left = serializers.IntegerField()
    op = serializers.ChoiceField(choices=OPERATORS)
    right = serializers.IntegerField()
    result = serializers.IntegerField()


class MathGameSerializer(serializers.Serializer):
    """The player's board. Results and the puzzle's secrets stay null until the game ends.

    ``solution``, ``min_operations`` and ``difficulty`` are secret while playing, since they
    hint at the answer.
    """

    date = serializers.DateField(source="math_puzzle.daily_puzzle.date")
    status = serializers.ChoiceField(choices=GameResult.Status.choices, source="result.status")
    target = serializers.IntegerField(source="math_puzzle.target")
    numbers = serializers.ListField(child=serializers.IntegerField(), source="math_puzzle.numbers")
    max_steps = serializers.SerializerMethodField()
    steps = serializers.SerializerMethodField()
    final_result = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    operations = serializers.SerializerMethodField()
    solved = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    duration_ms = serializers.SerializerMethodField()
    solution = serializers.SerializerMethodField()
    min_operations = serializers.SerializerMethodField()
    difficulty = serializers.SerializerMethodField()

    def _finished(self, game) -> bool:
        return game.result.status == GameResult.Status.COMPLETED

    def _detail(self, game, key: str):
        return game.result.details.get(key) if self._finished(game) else None

    def get_max_steps(self, game) -> int:
        return rules.MAX_STEPS

    @extend_schema_field(PlayedStepSerializer(many=True))
    def get_steps(self, game) -> list[dict]:
        return PlayedStepSerializer(game.result.details.get("steps", []), many=True).data

    def get_final_result(self, game) -> int | None:
        return self._detail(game, "final_result")

    def get_distance(self, game) -> int | None:
        return self._detail(game, "distance")

    def get_operations(self, game) -> int | None:
        return self._detail(game, "operations")

    def get_solved(self, game) -> bool | None:
        return game.result.solved if self._finished(game) else None

    def get_score(self, game) -> int | None:
        return game.result.score if self._finished(game) else None

    def get_duration_ms(self, game) -> int | None:
        return game.result.duration_ms if self._finished(game) else None

    # Secret until the game is finished: the example solution gives the answer away.
    @extend_schema_field(PlayedStepSerializer(many=True, allow_null=True))
    def get_solution(self, game) -> list[dict] | None:
        if not self._finished(game):
            return None
        return PlayedStepSerializer(game.math_puzzle.solution, many=True).data

    def get_min_operations(self, game) -> int | None:
        return game.math_puzzle.min_operations if self._finished(game) else None

    @extend_schema_field(serializers.ChoiceField(choices=DIFFICULTY_CHOICES, allow_null=True))
    def get_difficulty(self, game) -> str | None:
        return game.math_puzzle.difficulty if self._finished(game) else None
