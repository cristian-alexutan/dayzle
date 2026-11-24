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


def test_a_hint_takes_300_points_off_the_round_down_to_zero():
    assert rules.hinted_round_score(900, hinted=True) == 600
    assert rules.hinted_round_score(200, hinted=True) == 0
    assert rules.hinted_round_score(900, hinted=False) == 900


CLUJ_BOUNDS = Bounds(south=46.72, west=23.5, north=46.82, east=23.7)


def _off_center(center: Point, spot: Point) -> bool:
    distance = rules.distance_m(center, spot)
    return 0.25 * rules.HINT_RADIUS_M - 1 <= distance <= 0.75 * rules.HINT_RADIUS_M + 1


def test_the_hint_circle_holds_the_spot_but_is_never_centered_on_it():
    rng = random.Random(7)
    for _ in range(200):
        center = rules.hint_circle(PIATA_UNIRII, CLUJ_BOUNDS, rng)
        assert _off_center(center, PIATA_UNIRII)


def test_the_hint_circle_stays_inside_the_region_when_it_can():
    rng = random.Random(3)
    # 1.5 km inside the region's south-west corner: only circles leaning north-east fit.
    near_corner = Point(46.7335, 23.5197)
    for _ in range(100):
        center = rules.hint_circle(near_corner, CLUJ_BOUNDS, rng)
        assert rules.circle_overflow(center, rules.HINT_RADIUS_M, CLUJ_BOUNDS) == 0
        assert _off_center(center, near_corner)


def test_on_the_very_edge_the_hint_circle_leans_inside_as_far_as_it_can():
    rng = random.Random(5)
    on_edge = Point(46.72, 23.6)  # on the southern edge: no circle around it fits
    center = rules.hint_circle(on_edge, CLUJ_BOUNDS, rng)

    assert center.lat > on_edge.lat
    assert _off_center(center, on_edge)
    # Close to the best possible: the center 0.75 of the radius inside the edge.
    assert (
        rules.circle_overflow(center, rules.HINT_RADIUS_M, CLUJ_BOUNDS) < 0.3 * rules.HINT_RADIUS_M
    )


def test_circle_overflow_is_zero_inside_and_counts_each_side():
    middle = Point(46.77, 23.6)
    assert rules.circle_overflow(middle, 2500, CLUJ_BOUNDS) == 0
    assert rules.circle_overflow(Point(46.72, 23.6), 2500, CLUJ_BOUNDS) == 2500
