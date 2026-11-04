from datetime import timedelta

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.puzzles.models import Game
from apps.puzzles.tests.factories import DailyPuzzleFactory

from .factories import WordFactory, WordPuzzleFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("name", ["games_word_word_changelist", "games_word_wordpuzzle_changelist"])
def test_admin_pages_load(admin_client, name):
    WordPuzzleFactory()

    assert admin_client.get(reverse(f"admin:{name}")).status_code == 200


def test_admin_warns_when_the_word_was_used_on_another_day(admin_client):
    used = WordPuzzleFactory(answer=WordFactory(text="carte"))
    tomorrow = DailyPuzzleFactory(game=Game.WORD, date=used.daily_puzzle.date + timedelta(days=1))

    response = admin_client.post(
        reverse("admin:games_word_wordpuzzle_add"),
        {"daily_puzzle": tomorrow.pk, "answer": used.answer.pk},
        follow=True,
    )

    warnings = [str(m) for m in get_messages(response.wsgi_request)]
    assert any("is also the word of" in w for w in warnings)
