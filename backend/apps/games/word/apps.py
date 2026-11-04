from django.apps import AppConfig


class GamesWordConfig(AppConfig):
    name = "apps.games.word"
    label = "games_word"

    def ready(self) -> None:
        from apps.puzzles.registry import register_game

        from .models import WordPuzzle
        from .services import seed_puzzle

        register_game(key="word", name="Cuvantal", content_model=WordPuzzle, seed=seed_puzzle)
