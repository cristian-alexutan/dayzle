from django.apps import AppConfig


class GamesGeoConfig(AppConfig):
    name = "apps.games.geo"
    label = "games_geo"

    def ready(self) -> None:
        from apps.puzzles.registry import register_game

        from .models import GeoPuzzle
        from .services import seed_puzzle

        # Each day's game is made from random locations the first time someone opens it.
        register_game(
            key="geo",
            name="GeoGuesser",
            content_model=GeoPuzzle,
            seed=seed_puzzle,
            scheduled_by_admin=False,
        )
