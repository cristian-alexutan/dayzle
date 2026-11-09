"""API serializers for the Trivia game app."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.results.models import GameResult

from ..models import Category


class AnswerInputSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    choice = serializers.IntegerField()


class ChoiceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField()


class QuestionSerializer(serializers.Serializer):
    """A question as the player sees it: which choice is correct is never included."""

    id = serializers.IntegerField()
    category = serializers.ChoiceField(choices=Category.choices)
    text = serializers.CharField()
    choices = ChoiceSerializer(many=True, source="choices.all")


class AnswerSerializer(serializers.Serializer):
    """An answer the player gave, with the correct choice revealed."""

    question = serializers.IntegerField()
    choice = serializers.IntegerField()
    correct_choice = serializers.IntegerField()
    is_correct = serializers.BooleanField()


class TriviaGameSerializer(serializers.Serializer):
    """The player's quiz. The correct choice of a question is revealed only once it's answered.

    ``score``, ``solved`` and ``duration_ms`` stay null until the fifth answer.
    """

    date = serializers.DateField(source="puzzle.daily_puzzle.date")
    status = serializers.ChoiceField(choices=GameResult.Status.choices, source="result.status")
    questions = QuestionSerializer(many=True)
    answers = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    max_score = serializers.SerializerMethodField()
    solved = serializers.SerializerMethodField()
    duration_ms = serializers.SerializerMethodField()

    def _finished(self, game) -> bool:
        return game.result.status == GameResult.Status.COMPLETED

    @extend_schema_field(AnswerSerializer(many=True))
    def get_answers(self, game) -> list[dict]:
        return AnswerSerializer(game.result.details.get("answers", []), many=True).data

    def get_score(self, game) -> int | None:
        return game.result.score if self._finished(game) else None

    def get_max_score(self, game) -> int:
        return len(game.questions)

    def get_solved(self, game) -> bool | None:
        return game.result.solved if self._finished(game) else None

    def get_duration_ms(self, game) -> int | None:
        return game.result.duration_ms if self._finished(game) else None
