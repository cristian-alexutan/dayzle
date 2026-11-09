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
