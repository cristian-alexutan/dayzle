"""Make the coming days' Geo games in advance (they're otherwise made on first open)."""

from datetime import timedelta

from django.core.management.base import BaseCommand

from apps.common.time import today_in_romania
from apps.games.geo.selectors import active_regions
from apps.games.geo.services import ensure_daily_game
from apps.puzzles.exceptions import NoPuzzleError
from apps.puzzles.models import DailyPuzzle, Game


class Command(BaseCommand):
    help = "Make every active region's Geo game for today and the coming days."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7, help="Number of days to make.")

    def handle(self, *args, days: int, **options):
        today = today_in_romania()
        for offset in range(days):
            daily_puzzle, _ = DailyPuzzle.objects.get_or_create(
                game=Game.GEO, date=today + timedelta(days=offset)
            )
            for region in active_regions():
                try:
                    ensure_daily_game(daily_puzzle, region)
                except NoPuzzleError:
                    self.stderr.write(
                        f"{daily_puzzle.date}: {region.key} has too few locations; "
                        "run generate_locations."
                    )
        self.stdout.write(f"Geo games ready for {days} day(s).")
