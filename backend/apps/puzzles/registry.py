"""Registry of the games. Each game app registers itself from its AppConfig.ready()."""

from collections.abc import Callable
from dataclasses import dataclass

from django.core.exceptions import ImproperlyConfigured
from django.db import models

from .models import DailyPuzzle, Game


@dataclass(frozen=True)
class GameDefinition:
    key: str
    name: str
    content_model: type[models.Model]
    # Creates the game's content for a new calendar entry; used by `manage.py seed_dev`.
    seed: Callable[[DailyPuzzle], None] | None = None
    # False for a game that makes its own daily content (e.g. on first open), so the admin
    # doesn't warn about days with no puzzle yet.
    scheduled_by_admin: bool = True


_games: dict[str, GameDefinition] = {}


def register_game(
    *,
    key: str,
    name: str,
    content_model: type[models.Model],
    seed: Callable[[DailyPuzzle], None] | None = None,
    scheduled_by_admin: bool = True,
) -> GameDefinition:
    if key not in Game.values:
        raise ImproperlyConfigured(f"Unknown game {key!r}; add it to puzzles.models.Game.")
    if key in _games:
        raise ImproperlyConfigured(f"Game {key!r} is already registered.")
    definition = GameDefinition(
        key=key,
        name=name,
        content_model=content_model,
        seed=seed,
        scheduled_by_admin=scheduled_by_admin,
    )
    _games[key] = definition
    return definition


def get_games() -> list[GameDefinition]:
    return list(_games.values())
