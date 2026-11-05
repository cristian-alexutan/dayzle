from django.apps import AppConfig


class GamesMathConfig(AppConfig):
    name = "apps.games.math"
    label = "games_math"

    def ready(self) -> None:
        from apps.puzzles.registry import register_game

        from .models import MathPuzzle
        from .services import seed_puzzle

        register_game(
            key="math", name="Make the Target", content_model=MathPuzzle, seed=seed_puzzle
        )
