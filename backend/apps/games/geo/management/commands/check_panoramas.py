"""Recheck panoramas with Google: refresh their coordinates and deactivate removed ones."""

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError

from apps.common.time import today_in_romania
from apps.games.geo import services, streetview
from apps.games.geo.exceptions import StreetViewError
from apps.games.geo.models import Location
from apps.games.geo.selectors import locations_on_days


class Command(BaseCommand):
    help = (
        "Recheck the locations of the coming days' games (or the whole bank) with Google. "
        "Google only allows caching coordinates, so run it regularly. Needs "
        "GOOGLE_MAPS_SERVER_KEY."
    )

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7, help="Days from today to check.")
        parser.add_argument("--all", action="store_true", help="Check every active location.")

    def handle(self, *args, days: int, all: bool, **options):
        if not streetview.is_configured():
            raise CommandError("GOOGLE_MAPS_SERVER_KEY is not set.")
        if all:
            locations = Location.objects.filter(is_active=True)
        else:
            today = today_in_romania()
            locations = locations_on_days(today + timedelta(days=n) for n in range(days))
        locations = locations.select_related("region")
        try:
            report = services.recheck_locations(locations)
        except StreetViewError as error:
            raise CommandError(error.message) from None
        self.stdout.write(f"Checked {report.checked} location(s).")
        for location in report.removed:
            self.stderr.write(f"Removed by Google, deactivated: {location.panorama_id}")
        for location in report.outside:
            self.stderr.write(f"Moved outside its region, deactivated: {location.panorama_id}")
        if report.skipped:
            self.stderr.write(
                f"Skipped {report.skipped} after temporary Google errors; run it again for those."
            )
