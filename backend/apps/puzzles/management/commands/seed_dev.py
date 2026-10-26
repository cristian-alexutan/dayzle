"""Create local development data: an admin user and upcoming puzzles for registered games."""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.common.time import today_in_romania
from apps.puzzles.models import DailyPuzzle
from apps.puzzles.registry import get_games


class Command(BaseCommand):
    help = "Create a dev admin (admin/admin) and puzzles for today and the next days."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7, help="Number of days to fill.")

    def handle(self, *args, days: int, **options):
        if not settings.DEBUG:
            raise CommandError("seed_dev only runs with DEBUG enabled.")

        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin")
            self.stdout.write("Created superuser admin / admin")

        today = today_in_romania()
        for game in get_games():
            if game.seed is None:
                self.stdout.write(f"{game.key}: no seed hook, skipped")
                continue
            created = 0
            for offset in range(days):
                puzzle, is_new = DailyPuzzle.objects.get_or_create(
                    game=game.key, date=today + timedelta(days=offset)
                )
                if is_new:
                    game.seed(puzzle)
                    created += 1
            self.stdout.write(f"{game.key}: created {created} puzzle(s)")
