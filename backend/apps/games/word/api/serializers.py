"""API serializers for the Word game app."""

from rest_framework import serializers

from apps.results.models import GameResult

from .. import rules


class GuessInputSerializer(serializers.Serializer):
    guess = serializers.CharField(max_length=20, trim_whitespace=True)


class GuessSerializer(serializers.Serializer):
    word = serializers.CharField()
    colors = serializers.ListField(
        child=serializers.ChoiceField(choices=[rules.CORRECT, rules.PRESENT, rules.ABSENT])
    )


class WordGameSerializer(serializers.Serializer):
    """The player's board. ``answer``, ``solved`` and ``score`` stay null until the game ends."""

    date = serializers.DateField(source="word_puzzle.daily_puzzle.date")
    status = serializers.ChoiceField(choices=GameResult.Status.choices, source="result.status")
    word_length = serializers.SerializerMethodField()
    max_attempts = serializers.SerializerMethodField()
    guesses = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()
    solved = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    duration_ms = serializers.SerializerMethodField()

    def _finished(self, game) -> bool:
        return game.result.status == GameResult.Status.COMPLETED

    def get_word_length(self, game) -> int:
        return rules.WORD_LENGTH

    def get_max_attempts(self, game) -> int:
        return rules.MAX_ATTEMPTS

    @staticmethod
    def _guesses(game) -> list:
        return game.result.details.get("guesses", [])

    def get_guesses(self, game) -> list[dict]:
        return GuessSerializer(self._guesses(game), many=True).data

    # Secret until the game is finished: never reveal the answer while it can still be guessed.
    def get_answer(self, game) -> str | None:
        return game.word_puzzle.answer.text if self._finished(game) else None

    def get_solved(self, game) -> bool | None:
        return game.result.solved if self._finished(game) else None

    def get_score(self, game) -> int | None:
        return game.result.score if self._finished(game) else None

    def get_duration_ms(self, game) -> int | None:
        return game.result.duration_ms if self._finished(game) else None
