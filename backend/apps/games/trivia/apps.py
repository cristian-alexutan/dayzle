from django.apps import AppConfig


class GamesTriviaConfig(AppConfig):
    name = "apps.games.trivia"
    label = "games_trivia"

    def ready(self) -> None:
        from apps.puzzles.registry import register_game

        from .models import TriviaPuzzle
        from .services import seed_puzzle

        register_game(key="trivia", name="Trivia", content_model=TriviaPuzzle, seed=seed_puzzle)
