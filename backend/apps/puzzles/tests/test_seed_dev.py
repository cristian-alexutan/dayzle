import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command

from apps.puzzles.models import DailyPuzzle

pytestmark = pytest.mark.django_db


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
