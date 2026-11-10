import pytest

from apps.games.logic import rules
from apps.games.logic.rules import DEMO_REGIONS, DEMO_SIZE, DEMO_SOLUTION


def test_demo_level_is_valid():
    assert rules.validate_puzzle(DEMO_SIZE, DEMO_REGIONS, DEMO_SOLUTION) == []


def test_demo_level_has_exactly_one_solution():
    assert rules.count_solutions(DEMO_REGIONS) == 1


def test_touches_includes_diagonals():
    assert rules.touches((2, 2), (3, 3))
    assert rules.touches((2, 2), (2, 3))
    assert not rules.touches((2, 2), (4, 2))
    assert not rules.touches((2, 2), (2, 2))


def test_no_conflicts_on_an_empty_board():
    assert rules.conflicts((0, 2), [], DEMO_REGIONS) == []


def test_conflict_on_the_same_row():
    assert rules.conflicts((0, 5), [(0, 2)], DEMO_REGIONS) == [(0, 2)]


def test_conflict_on_the_same_column():
    assert rules.conflicts((5, 2), [(0, 2)], DEMO_REGIONS) == [(0, 2)]


def test_conflict_in_the_same_region():
    # (3, 0) and (4, 2) are both in region 3, on different rows and columns, and don't touch.
    assert rules.conflicts((4, 2), [(3, 0)], DEMO_REGIONS) == [(3, 0)]


def test_conflict_when_suns_touch_diagonally():
    # (2, 4) is in region 2 and (3, 3) in region 4, so touching is the only broken rule.
    assert rules.conflicts((3, 3), [(2, 4)], DEMO_REGIONS) == [(2, 4)]


def test_only_the_conflicting_suns_are_returned():
    suns = [(0, 2), (1, 0)]
    assert rules.conflicts((0, 5), suns, DEMO_REGIONS) == [(0, 2)]


def test_is_in_grid():
    assert rules.is_in_grid((0, 0), 6)
    assert rules.is_in_grid((5, 5), 6)
    assert not rules.is_in_grid((6, 0), 6)
    assert not rules.is_in_grid((0, -1), 6)


def test_validate_rejects_a_wrong_number_of_regions():
    regions = [row[:] for row in DEMO_REGIONS]
    regions[5] = [4] * 6  # region 5 disappears
    assert rules.validate_puzzle(DEMO_SIZE, regions, DEMO_SOLUTION)


@pytest.mark.parametrize("size", [3, 10])
def test_validate_rejects_grids_too_small_or_too_large(size):
    regions = [[row] * size for row in range(size)]
    solution = list(range(size))
    assert rules.validate_puzzle(size, regions, solution) == [
        "The grid must be from 4 × 4 to 9 × 9."
    ]


def test_validate_rejects_a_solution_that_breaks_a_rule():
    solution = [2, 3, 4, 1, 0, 5]  # rows 0 and 1 touch
    assert rules.validate_puzzle(DEMO_SIZE, DEMO_REGIONS, solution)


def test_validate_rejects_a_grid_with_several_solutions():
    # 5 × 5 grid with one region per row: rows are independent, so many solutions exist.
    regions = [[row] * 5 for row in range(5)]
    solution = [0, 2, 4, 1, 3]
    assert rules.validate_puzzle(5, regions, solution) == ["The grid has more than one solution."]


def test_the_demo_regions_are_all_connected():
    assert rules.split_regions(DEMO_REGIONS) == []


def test_a_region_in_two_pieces_is_found():
    regions = [
        [0, 1, 0],
        [2, 1, 1],
        [2, 2, 2],
    ]
    assert rules.split_regions(regions) == [0]


def test_cells_touching_only_diagonally_are_not_connected():
    regions = [
        [0, 1],
        [1, 0],
    ]
    assert rules.split_regions(regions) == [0, 1]


def test_validate_rejects_a_split_region():
    regions = [row[:] for row in DEMO_REGIONS]
    regions[5][0] = 0  # a lone cell of region 0, far from the rest of it
    problems = rules.validate_puzzle(DEMO_SIZE, regions, DEMO_SOLUTION)
    assert problems == ["Every region must be one connected piece; these are split: 0."]


def test_the_board_is_full_with_one_sun_per_row():
    all_suns = list(enumerate(DEMO_SOLUTION))
    assert rules.is_full(all_suns, DEMO_SIZE)
    assert not rules.is_full(all_suns[:-1], DEMO_SIZE)


def test_score_example_from_the_review():
    # 6 × 6 in 3 minutes with 1 mistake: 1000 × (1 − 3 / 12) − 50 = 700.
    assert rules.score(6, duration_ms=3 * 60_000, mistakes=1) == 700


def test_score_is_1000_for_an_instant_solve_with_no_mistakes():
    assert rules.score(6, duration_ms=0, mistakes=0) == 1000


def test_the_time_limit_grows_with_the_grid():
    # Half of the limit is used: 6 of 12 minutes, or 9 of 18.
    assert rules.score(6, duration_ms=6 * 60_000, mistakes=0) == 500
    assert rules.score(9, duration_ms=9 * 60_000, mistakes=0) == 500


def test_the_score_never_goes_below_zero():
    assert rules.score(6, duration_ms=60 * 60_000, mistakes=0) == 0
    assert rules.score(6, duration_ms=0, mistakes=30) == 0
