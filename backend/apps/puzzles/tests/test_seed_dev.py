from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command

from apps.common.time import today_in_romania
from apps.puzzles.models import DailyPuzzle

pytestmark = pytest.mark.django_db


class ContentWithNoRows:
    """A stand-in content model linked by ``daily_puzzle`` that has no entry for any day."""

    _meta = SimpleNamespace(get_fields=lambda: [SimpleNamespace(name="daily_puzzle")])
    objects = SimpleNamespace(filter=lambda **lookup: SimpleNamespace(exists=lambda: False))


def test_seed_dev_creates_admin_and_seeds_registered_games(settings, clean_registry):
    settings.DEBUG = True
    seeded = []
    clean_registry.register_game(
        key="word", name="Word", content_model=DailyPuzzle, seed=seeded.append
    )

    call_command("seed_dev", days=3)
    call_command("seed_dev", days=3)  # running it again creates nothing new

    assert get_user_model().objects.filter(username="admin", is_superuser=True).exists()
    assert DailyPuzzle.objects.filter(game="word").count() == 3
    assert len(seeded) == 3


def test_seed_dev_refuses_to_run_without_debug(settings):
    settings.DEBUG = False

    with pytest.raises(CommandError):
        call_command("seed_dev")


def test_seed_dev_seeds_existing_days_that_have_no_content(settings, clean_registry):
    """A day left without content (e.g. a run that failed half-way) is seeded on the next run."""
    settings.DEBUG = True
    seeded = []
    clean_registry.register_game(
        key="word", name="Word", content_model=ContentWithNoRows, seed=seeded.append
    )
    DailyPuzzle.objects.create(game="word", date=today_in_romania())

    call_command("seed_dev", days=2)

    assert [puzzle.date for puzzle in seeded] == [
        today_in_romania(),
        today_in_romania() + timedelta(days=1),
    ]
