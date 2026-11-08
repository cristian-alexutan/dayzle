import random

import pytest

from apps.games.geo import rules
from apps.games.geo.rules import Bounds, Point

PIATA_UNIRII = Point(46.76946, 23.58993)
PIATA_MUZEULUI = Point(46.77144, 23.58733)


def test_distance_is_zero_for_the_same_point():
    assert rules.distance_m(PIATA_UNIRII, PIATA_UNIRII) == 0


def test_distance_matches_a_known_distance():
    # One degree of latitude is about 111.2 km on a sphere of radius 6371 km.
    assert rules.distance_m(Point(46, 23), Point(47, 23)) == pytest.approx(111_195, abs=1)


def test_distance_between_two_squares_in_cluj():
    assert rules.distance_m(PIATA_UNIRII, PIATA_MUZEULUI) == pytest.approx(298, abs=5)


def test_distance_is_symmetric():
    there = rules.distance_m(PIATA_UNIRII, PIATA_MUZEULUI)
    back = rules.distance_m(PIATA_MUZEULUI, PIATA_UNIRII)
    assert there == pytest.approx(back)


@pytest.mark.parametrize(
    ("distance", "points"),
    [(0, 1000), (25, 1000), (26, 983), (100, 936), (500, 717), (1000, 513), (3000, 135)],
)
def test_round_score_with_the_cluj_scale(distance, points):
    assert rules.round_score(distance, 1500) == points


def test_round_score_reaches_zero_far_away():
    assert rules.round_score(50_000, 1500) == 0


def test_a_larger_scale_is_more_forgiving():
    assert rules.round_score(5000, 50_000) > rules.round_score(5000, 1500)


def test_total_and_solved_threshold():
    assert rules.total_score([1000, 500, 0, 250, 750]) == 2500
    assert rules.is_solved(2500)
    assert not rules.is_solved(2499)
    assert rules.MAX_SCORE == 5000


def test_bounds_contain_their_edges_and_nothing_outside():
    bounds = Bounds(south=46.0, west=23.0, north=47.0, east=24.0)

    assert bounds.contains(Point(46.0, 23.0))
    assert bounds.contains(Point(47.0, 24.0))
    assert not bounds.contains(Point(47.01, 23.5))
    assert not bounds.contains(Point(46.5, 22.99))


def test_random_points_stay_inside_and_repeat_with_a_seed():
    bounds = Bounds(south=46.0, west=23.0, north=47.0, east=24.0)

    first = [bounds.random_point(random.Random(3)) for _ in range(1)]
    again = [bounds.random_point(random.Random(3)) for _ in range(1)]
    many = [bounds.random_point(random.Random(n)) for n in range(200)]

    assert first == again
    assert all(bounds.contains(point) for point in many)


def test_spacing():
    assert rules.is_spaced([PIATA_UNIRII, PIATA_MUZEULUI], 250)
    assert not rules.is_spaced([PIATA_UNIRII, PIATA_MUZEULUI], 1000)
    assert rules.is_spaced([PIATA_UNIRII], 1000)
