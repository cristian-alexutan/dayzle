"""Trivia scores are now stored in half points (see ``rules.SCORE_SCALE``): double the old ones."""

from django.db import migrations
from django.db.models import F

GAME = "trivia"


def to_half_points(apps, schema_editor):
    GameResult = apps.get_model("results", "GameResult")
    GameResult.objects.filter(daily_puzzle__game=GAME).update(score=F("score") * 2)


def to_whole_points(apps, schema_editor):
    GameResult = apps.get_model("results", "GameResult")
    GameResult.objects.filter(daily_puzzle__game=GAME).update(score=F("score") / 2)


class Migration(migrations.Migration):
    dependencies = [
        ("games_trivia", "0001_question_bank"),
        ("results", "0002_active_play_time"),
    ]

    operations = [migrations.RunPython(to_half_points, to_whole_points)]
