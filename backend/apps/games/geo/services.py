"""Write operations and business rules for the GeoGuesser game app."""

import logging
import random
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.common.time import today_in_romania
from apps.puzzles.exceptions import NoPuzzleError
from apps.puzzles.models import DailyPuzzle, Game
from apps.puzzles.selectors import get_playable_puzzle
from apps.results.exceptions import AlreadyPlayedError
from apps.results.models import GameResult
from apps.results.selectors import get_result
from apps.results.services import complete, save_progress, start_or_resume

from . import rules, streetview
from .exceptions import AlreadyAnsweredError, InvalidGuessError, RegionLockedError
from .models import GeoPuzzle, GeoPuzzleLocation, Location, Region
from .selectors import (
    active_location_count,
    active_regions,
    get_active_region,
    get_geo_puzzle,
    ordered_locations,
    pick_locations,
)

logger = logging.getLogger(__name__)

# How far from a random point generate_locations looks for a panorama.
SEARCH_RADIUS_M = 100
# Random points tried per location wanted before generate_locations gives up.
ATTEMPTS_PER_LOCATION = 20
# seed_dev fills a region's bank up to a week's worth of games (with room for the spacing
# rule) when it has fewer than two games' worth.
SEED_BANK_SIZE = 7 * rules.ROUNDS * 2
SEED_BANK_MINIMUM = 2 * rules.ROUNDS


@dataclass(frozen=True)
class GeoGame:
    """A player's daily game: their result, the region's game and its locations by round."""

    result: GameResult
    puzzle: GeoPuzzle
    locations: list[Location]


# Daily games


def _create_puzzle(daily_puzzle: DailyPuzzle, region: Region, rng: random.Random) -> GeoPuzzle:
    locations = pick_locations(region, rng)
    if len(locations) < rules.ROUNDS:
        logger.warning("Geo region %s has too few spaced locations for a game.", region.key)
        raise NoPuzzleError()
    with transaction.atomic():
        puzzle = GeoPuzzle.objects.create(daily_puzzle=daily_puzzle, region=region)
        GeoPuzzleLocation.objects.bulk_create(
            GeoPuzzleLocation(puzzle=puzzle, location=location, position=position)
            for position, location in enumerate(locations, start=1)
        )
    return puzzle


def ensure_daily_game(
    daily_puzzle: DailyPuzzle, region: Region, rng: random.Random | None = None
) -> GeoPuzzle:
    """The region's game for this day, made from random locations if it doesn't exist yet.

    Safe when several requests make it at once: one wins and the others load its game.
    """
    puzzle = get_geo_puzzle(daily_puzzle, region)
    if puzzle is None:
        try:
            _create_puzzle(daily_puzzle, region, rng or random.Random())
        except IntegrityError:
            pass  # another request made it first
        puzzle = get_geo_puzzle(daily_puzzle, region)
    if puzzle is None or len(puzzle.entries.all()) != rules.ROUNDS:
        raise NoPuzzleError()
    return puzzle


def get_playable_day(day: date) -> DailyPuzzle:
    """The Geo calendar entry for a playable day, made for today if it doesn't exist yet.

    Other days follow the shared rules (``archive_unavailable``, ``no_puzzle``).
    """
    if day == today_in_romania():
        DailyPuzzle.objects.get_or_create(game=Game.GEO, date=day)
    return get_playable_puzzle(Game.GEO, day)


# Playing


def open_game(guest_id: uuid.UUID, region_key: str | None, day: date) -> GeoGame:
    """Return the player's game for the day, starting it (and its clock) on first open.

    The first region a player opens is theirs for the day: opening another one raises
    ``RegionLockedError``.
    """
    region = get_active_region(region_key)
    daily_puzzle = get_playable_day(day)
    existing = get_result(guest_id, daily_puzzle)
    if existing is not None and existing.details.get("region") not in (None, region.key):
        raise RegionLockedError(details={"region": existing.details["region"]})
    puzzle = ensure_daily_game(daily_puzzle, region)
    result = start_or_resume(guest_id, daily_puzzle)
    if result.details.get("region") is None and result.status == GameResult.Status.IN_PROGRESS:
        with transaction.atomic():
            locked = GameResult.objects.select_for_update().get(pk=result.pk)
            if locked.details.get("region") is None:
                locked = save_progress(locked, {"region": region.key, "guesses": []})
            result = locked
    played = result.details.get("region")
    if played != region.key:
        raise RegionLockedError(details={"region": played})
    return GeoGame(result, puzzle, ordered_locations(puzzle))


def guess(
    guest_id: uuid.UUID,
    region_key: str | None,
    day: date,
    round_number: int,
    lat: float,
    lng: float,
) -> GeoGame:
    """Score a guess for the current round and reveal that round's location.

    Rounds are guessed in order, once each. A guess outside the region is refused without
    using up the round. The fifth guess finishes the game with the sum of the round scores.
    """
    game = open_game(guest_id, region_key, day)
    region = game.puzzle.region
    point = rules.Point(lat, lng)
    with transaction.atomic():
        # Lock the result so two simultaneous guesses can't both count for the same round.
        result = GameResult.objects.select_for_update().get(pk=game.result.pk)
        if result.status == GameResult.Status.COMPLETED:
            raise AlreadyPlayedError()
        guesses = result.details.get("guesses", [])
        current = len(guesses) + 1
        if round_number < current:
            raise AlreadyAnsweredError()
        if round_number != current:
            raise InvalidGuessError(
                f"Round {current} is the one to guess.", details={"current_round": current}
            )
        if not region.bounds.contains(point):
            raise InvalidGuessError(
                f"The guess must be inside {region.name}.", details={"bounds": "outside"}
            )

        distance = rules.distance_m(point, game.locations[current - 1].point)
        guesses = [
            *guesses,
            {
                "round": current,
                "lat": lat,
                "lng": lng,
                "distance_m": round(distance),
                "score": rules.round_score(distance, region.score_scale_m),
            },
        ]
        details = {"region": region.key, "guesses": guesses}
        if len(guesses) == rules.ROUNDS:
            total = rules.total_score(given["score"] for given in guesses)
            result = complete(result, solved=rules.is_solved(total), score=total, details=details)
        else:
            result = save_progress(result, details)
    return GeoGame(result, game.puzzle, game.locations)


# Location bank


@dataclass
class GenerationReport:
    added: int = 0
    attempts: int = 0


def generate_locations(
    region: Region, count: int, rng: random.Random | None = None
) -> GenerationReport:
    """Add up to ``count`` random Google panoramas inside the region to its location bank.

    Each try picks a random point in the region and asks Google for the nearest outdoor
    panorama. Stops after ``ATTEMPTS_PER_LOCATION`` tries per location wanted.
    """
    rng = rng or random.Random()
    report = GenerationReport()
    known = set(Location.objects.values_list("panorama_id", flat=True))
    while report.added < count and report.attempts < count * ATTEMPTS_PER_LOCATION:
        report.attempts += 1
        start = region.bounds.random_point(rng)
        panorama = streetview.find_panorama(start.lat, start.lng, SEARCH_RADIUS_M)
        if panorama is None or panorama.pano_id in known:
            continue
        if not region.bounds.contains(rules.Point(panorama.lat, panorama.lng)):
            continue
        Location.objects.create(
            region=region,
            panorama_id=panorama.pano_id,
            latitude=panorama.lat,
            longitude=panorama.lng,
            last_checked_at=timezone.now(),
        )
        known.add(panorama.pano_id)
        report.added += 1
    return report


@dataclass
class RecheckReport:
    checked: int = 0
    removed: list[Location] = field(default_factory=list)


def recheck_locations(locations: Iterable[Location]) -> RecheckReport:
    """Refresh the locations' coordinates from Google, deactivating panoramas it removed.

    Google allows keeping panorama IDs, but coordinates only as a cache, so run this regularly.
    """
    report = RecheckReport()
    for location in locations:
        panorama = streetview.get_panorama(location.panorama_id)
        report.checked += 1
        location.last_checked_at = timezone.now()
        if panorama is None:
            location.is_active = False
            report.removed.append(location)
        else:
            location.latitude, location.longitude = panorama.lat, panorama.lng
        location.save(update_fields=["latitude", "longitude", "is_active", "last_checked_at"])
    return report


def seed_puzzle(daily_puzzle: DailyPuzzle) -> None:
    """``seed_dev`` hook: make every active region's game for a new day.

    Generates a week's worth of locations first for a region whose bank is too small, which
    needs ``GOOGLE_MAPS_SERVER_KEY``. Without it, regions with no bank are skipped.
    """
    for region in active_regions():
        size = active_location_count(region)
        if size < SEED_BANK_MINIMUM:
            if not streetview.is_configured():
                logger.warning(
                    "Geo: no location bank for %s and GOOGLE_MAPS_SERVER_KEY is not set; skipped.",
                    region.key,
                )
                continue
            generate_locations(region, SEED_BANK_SIZE - size)
        try:
            ensure_daily_game(daily_puzzle, region)
        except NoPuzzleError:
            continue
