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


def test_is_correct():
    assert rules.is_correct((0, 2), DEMO_SOLUTION)
    assert not rules.is_correct((0, 3), DEMO_SOLUTION)


def test_is_solved_only_with_every_sun_of_the_solution():
    all_suns = [(row, col) for row, col in enumerate(DEMO_SOLUTION)]
    assert rules.is_solved(all_suns, DEMO_SOLUTION)
    assert not rules.is_solved(all_suns[:-1], DEMO_SOLUTION)


def test_is_in_grid():
    assert rules.is_in_grid((0, 0), 6)
    assert rules.is_in_grid((5, 5), 6)
    assert not rules.is_in_grid((6, 0), 6)
    assert not rules.is_in_grid((0, -1), 6)


def test_validate_rejects_a_wrong_number_of_regions():
    regions = [row[:] for row in DEMO_REGIONS]
    regions[5] = [4] * 6  # region 5 disappears
    assert rules.validate_puzzle(DEMO_SIZE, regions, DEMO_SOLUTION)


def test_validate_rejects_a_solution_that_breaks_a_rule():
    solution = [2, 3, 4, 1, 0, 5]  # rows 0 and 1 touch
    assert rules.validate_puzzle(DEMO_SIZE, DEMO_REGIONS, solution)


def test_validate_rejects_a_grid_with_several_solutions():
    # 5 × 5 grid with one region per row: rows are independent, so many solutions exist.
    regions = [[row] * 5 for row in range(5)]
    solution = [0, 2, 4, 1, 3]
    assert rules.validate_puzzle(5, regions, solution) == ["The grid has more than one solution."]


def test_combo_points_grow_with_the_streak():
    assert rules.combo_points([True, True, True]) == 1 + 2 + 3


def test_a_mistake_resets_the_streak():
    # 1 + 2 + 3, mistake, then 1 + 2 + 3 again
    assert rules.combo_points([True, True, True, False, True, True, True]) == 12


def test_mistakes_alone_give_no_combo_points():
    assert rules.combo_points([False, False]) == 0


def test_max_combo_points():
    assert rules.max_combo_points(6) == 21
    assert rules.max_combo_points(9) == 45


def test_score_examples_from_the_documentation():
    perfect = [True] * 6
    one_mistake = [True, True, True, False, True, True, True]
    assert rules.score(perfect, 6, duration_ms=2 * 60_000) == 900
    assert rules.score(perfect, 6, duration_ms=4 * 60_000) == 800
    assert rules.score(one_mistake, 6, duration_ms=4 * 60_000) == 500


def test_score_is_1000_at_most_and_time_points_never_go_negative():
    assert rules.score([True] * 6, 6, duration_ms=0) == 1000
    assert rules.score([True] * 6, 6, duration_ms=60 * 60_000) == 700


def test_every_grid_size_can_reach_the_same_combo_maximum():
    slow = 60 * 60_000  # long enough to get no time points
    assert rules.score([True] * 6, 6, slow) == rules.score([True] * 9, 9, slow) == 700


def test_current_streak_counts_the_correct_suns_since_the_last_mistake():
    assert rules.current_streak([]) == 0
    assert rules.current_streak([True, True]) == 2
    assert rules.current_streak([True, True, False]) == 0
    assert rules.current_streak([True, False, True]) == 1


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
