from django.apps import AppConfig


class PuzzlesConfig(AppConfig):
    name = "apps.puzzles"
    label = "puzzles"

    def ready(self) -> None:
        from django.urls import register_converter

        from .converters import GameDayConverter

        # Game URLs use <game_day:day>, e.g. /api/v1/games/word/today/
        register_converter(GameDayConverter, "game_day")
