from django.apps import AppConfig


class GamesLogicConfig(AppConfig):
    name = "apps.games.logic"
    label = "games_logic"

    def ready(self) -> None:
        from apps.puzzles.registry import register_game

        from .models import LogicPuzzle
        from .services import seed_puzzle

        register_game(key="logic", name="Sunspots", content_model=LogicPuzzle, seed=seed_puzzle)
