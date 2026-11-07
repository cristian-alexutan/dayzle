"""Fill a region's location bank with random Google Street View panoramas."""

import random

from django.core.management.base import BaseCommand, CommandError

from apps.games.geo import services, streetview
from apps.games.geo.exceptions import StreetViewError, UnknownRegionError
from apps.games.geo.selectors import get_active_region


class Command(BaseCommand):
    help = (
        "Add random outdoor Google panoramas inside a region to its location bank. "
        "Needs GOOGLE_MAPS_SERVER_KEY."
    )

    def add_arguments(self, parser):
        parser.add_argument("--region", help="Region key (default: the default region).")
        parser.add_argument("--count", type=int, default=50, help="Locations to add.")
        parser.add_argument("--seed", type=int, help="Random seed, for repeatable runs.")

    def handle(self, *args, region: str | None, count: int, seed: int | None, **options):
        if not streetview.is_configured():
            raise CommandError("GOOGLE_MAPS_SERVER_KEY is not set.")
        try:
            target = get_active_region(region)
            report = services.generate_locations(target, count, random.Random(seed))
        except (UnknownRegionError, StreetViewError) as error:
            raise CommandError(error.message) from None
        self.stdout.write(
            f"{target.key}: added {report.added} location(s) in {report.attempts} tries"
            + (f" ({report.errors} temporary Google error(s))." if report.errors else ".")
        )
        if report.added < count:
            self.stderr.write(f"Only {report.added} of {count} found; run it again for more.")
