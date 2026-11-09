"""Read queries for the GeoGuesser game app."""

import random
from collections.abc import Iterable
from datetime import date, timedelta

from django.db.models import Count, Max, Prefetch, QuerySet
from django.utils import timezone

from apps.puzzles.models import DailyPuzzle, Game
from apps.results.models import GameResult

from . import rules
from .exceptions import UnknownRegionError
from .models import GeoPuzzle, GeoPuzzleLocation, Location, Region

# Google lets us keep a panorama's coordinates only as a cache (30 days at most, as far as we
# know), so locations not rechecked since then aren't used in new games until check_panoramas
# refreshes them.
COORDINATES_FRESH_FOR = timedelta(days=30)


def active_regions() -> QuerySet[Region]:
    """The regions players can choose from, the default one first."""
    return Region.objects.filter(is_active=True)


def get_active_region(key: str | None = None) -> Region:
    """The region with this key, or the default region when no key is given."""
    regions = active_regions()
    region = regions.filter(key=key).first() if key else regions.filter(is_default=True).first()
    if region is None:
        raise UnknownRegionError()
    return region


def has_players(daily_puzzle: DailyPuzzle) -> bool:
    """Whether anyone has opened this day's game, in any region. From then on it can't change."""
    return GameResult.objects.filter(daily_puzzle=daily_puzzle).exists()


def get_geo_puzzle(daily_puzzle: DailyPuzzle, region: Region) -> GeoPuzzle | None:
    """The region's game for this day with its locations prefetched, if it has been made."""
    entries = GeoPuzzleLocation.objects.select_related("location")
    return (
        GeoPuzzle.objects.select_related("daily_puzzle", "region")
        .prefetch_related(Prefetch("entries", queryset=entries))
        .filter(daily_puzzle=daily_puzzle, region=region)
        .first()
    )


def ordered_locations(puzzle: GeoPuzzle) -> list[Location]:
    """The game's locations by round, using the prefetched entries when available."""
    return [entry.location for entry in puzzle.entries.all()]


def usable_locations(region: Region) -> QuerySet[Location]:
    """The region's locations a new game can use: active, with recently checked coordinates."""
    return Location.objects.filter(
        region=region,
        is_active=True,
        last_checked_at__gte=timezone.now() - COORDINATES_FRESH_FOR,
    )


def active_location_count(region: Region) -> int:
    return Location.objects.filter(region=region, is_active=True).count()


def pick_locations(region: Region, rng: random.Random, count: int = rules.ROUNDS) -> list[Location]:
    """A day's worth of locations: least used first, at least ``min_spacing_m`` apart.

    Only usable locations (see ``usable_locations``). Fewer than ``count`` only if the bank is
    too small, too clustered or not rechecked recently.
    """
    candidates = list(usable_locations(region).annotate(uses=Count("entries", distinct=True)))
    # Random order within each usage count, so equally used locations are picked fairly.
    rng.shuffle(candidates)
    candidates.sort(key=lambda location: location.uses)
    picked: list[Location] = []
    for location in candidates:
        if rules.is_spaced([*(p.point for p in picked), location.point], region.min_spacing_m):
            picked.append(location)
            if len(picked) == count:
                break
    return picked


def last_used_dates() -> QuerySet[Location]:
    """Locations annotated with ``last_used``: the latest day they were in a game."""
    return Location.objects.annotate(last_used=Max("entries__puzzle__daily_puzzle__date"))


def locations_on_days(days: Iterable[date]) -> QuerySet[Location]:
    """The locations of the games made for these days."""
    return Location.objects.filter(
        entries__puzzle__daily_puzzle__game=Game.GEO,
        entries__puzzle__daily_puzzle__date__in=list(days),
    ).distinct()
