"""Rules of the GeoGuesser game that need no database: distances, bounds, spacing and scoring."""

import math
import random
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

ROUNDS = 5
MAX_ROUND_SCORE = 1000
MAX_SCORE = ROUNDS * MAX_ROUND_SCORE
# A guess this close to the real spot gets the full round score.
FULL_SCORE_RADIUS_M = 25
# A game counts as solved with at least half of the maximum score.
SOLVED_AT = MAX_SCORE // 2

EARTH_RADIUS_M = 6_371_000
METRES_PER_DEGREE = 111_320

# A hint draws a circle around the round's spot, 5 km wide (2.5 km radius), and takes this many
# points off the round, down to 0. One hint per round.
HINT_RADIUS_M = 2500
HINT_PENALTY = 300
# How far the circle's center is from the spot, as a share of the radius: never in the center,
# never on the edge.
HINT_OFFSET = (0.25, 0.75)
# Random circles hint_circle tries, looking for one that stays inside the region.
HINT_TRIES = 500


@dataclass(frozen=True)
class Point:
    lat: float
    lng: float


@dataclass(frozen=True)
class Bounds:
    """A region's bounding box. Guesses and locations must lie inside it."""

    south: float
    west: float
    north: float
    east: float

    def contains(self, point: Point) -> bool:
        return self.south <= point.lat <= self.north and self.west <= point.lng <= self.east

    def random_point(self, rng: random.Random) -> Point:
        return Point(rng.uniform(self.south, self.north), rng.uniform(self.west, self.east))


def distance_m(a: Point, b: Point) -> float:
    """Great-circle distance in metres between two points (haversine formula)."""
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    d_lat = lat2 - lat1
    d_lng = math.radians(b.lng - a.lng)
    h = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lng / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(min(1.0, h)))


def round_score(distance: float, scale_m: float) -> int:
    """Points for one round: ``round(1000 × e^(−d / scale))``, and 1000 within 25 m.

    ``scale_m`` is set per region, so a guess 1 km off counts for more in a country than in a
    city. With Cluj-Napoca's 1500 m: 100 m → 936, 500 m → 717, 1 km → 513, 3 km → 135.
    """
    if distance <= FULL_SCORE_RADIUS_M:
        return MAX_ROUND_SCORE
    return round(MAX_ROUND_SCORE * math.exp(-distance / scale_m))


def hinted_round_score(score: int, hinted: bool) -> int:
    """A round's points after its hint, if it had one: ``HINT_PENALTY`` less, down to 0."""
    return max(0, score - HINT_PENALTY) if hinted else score


def _offset(spot: Point, distance: float, bearing: float) -> Point:
    """The point ``distance`` metres from ``spot`` in direction ``bearing`` (0 is north)."""
    d_lat = distance * math.cos(bearing) / METRES_PER_DEGREE
    d_lng = distance * math.sin(bearing) / (METRES_PER_DEGREE * math.cos(math.radians(spot.lat)))
    return Point(spot.lat + d_lat, spot.lng + d_lng)


def circle_overflow(center: Point, radius_m: float, bounds: Bounds) -> float:
    """How far, in metres summed over the four sides, a circle sticks out of ``bounds`` (0 when
    it lies inside)."""
    lng_metres = METRES_PER_DEGREE * math.cos(math.radians(center.lat))
    room = (
        (bounds.north - center.lat) * METRES_PER_DEGREE,
        (center.lat - bounds.south) * METRES_PER_DEGREE,
        (bounds.east - center.lng) * lng_metres,
        (center.lng - bounds.west) * lng_metres,
    )
    return sum(max(0.0, radius_m - side) for side in room)


def hint_circle(spot: Point, bounds: Bounds, rng: random.Random) -> Point:
    """The center of a hint circle of ``HINT_RADIUS_M`` that holds ``spot``, off its center.

    The center is a random distance (``HINT_OFFSET`` of the radius) in a random direction from
    the spot, so the spot is always inside but never in the middle. Of ``HINT_TRIES`` such
    circles, the first that lies inside ``bounds`` is used, so none of it covers ground no spot
    can be on; near the region's edge, where none fits, the one that sticks out least.
    """
    best, best_overflow = None, math.inf
    for _ in range(HINT_TRIES):
        center = _offset(
            spot, rng.uniform(*HINT_OFFSET) * HINT_RADIUS_M, rng.uniform(0, 2 * math.pi)
        )
        overflow = circle_overflow(center, HINT_RADIUS_M, bounds)
        if overflow == 0:
            return center
        if overflow < best_overflow:
            best, best_overflow = center, overflow
    return best


def total_score(round_scores: Iterable[int]) -> int:
    """The game's score: the sum of its rounds, 0 to 5000. Ties are broken by ``duration_ms``."""
    return sum(round_scores)


def is_solved(total: int) -> bool:
    return total >= SOLVED_AT


def is_spaced(points: Sequence[Point], min_spacing_m: float) -> bool:
    """Whether every two points are at least ``min_spacing_m`` apart."""
    return all(
        distance_m(a, b) >= min_spacing_m
        for index, a in enumerate(points)
        for b in points[index + 1 :]
    )
