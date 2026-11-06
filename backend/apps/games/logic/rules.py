"""Rules of the Logic game (Sunspots), with no Django code.

The grid is ``size`` × ``size`` cells, divided into ``size`` colored regions. The player places one
sun in every row, every column and every region, and no two suns may touch, not even diagonally.

A cell is a ``(row, col)`` pair, counted from 0. ``regions[row][col]`` is the region number of a
cell (0 to size - 1), and ``solution[row]`` is the column of the sun on that row.
"""

Cell = tuple[int, int]
Regions = list[list[int]]

# The hand-made level used until the generator exists. It has exactly one solution
# (``tests/test_rules.py`` checks it with ``count_solutions``).
DEMO_SIZE = 6
DEMO_REGIONS: Regions = [
    [1, 0, 0, 0, 2, 2],
    [1, 1, 2, 2, 2, 2],
    [1, 1, 4, 4, 2, 2],
    [3, 3, 3, 4, 2, 2],
    [5, 5, 3, 4, 5, 5],
    [5, 5, 5, 5, 5, 5],
]
DEMO_SOLUTION = [2, 0, 4, 1, 3, 5]


def is_in_grid(cell: Cell, size: int) -> bool:
    row, col = cell
    return 0 <= row < size and 0 <= col < size


def touches(a: Cell, b: Cell) -> bool:
    """Two different cells touch when they are neighbors, diagonals included."""
    return a != b and abs(a[0] - b[0]) <= 1 and abs(a[1] - b[1]) <= 1


def conflicts(cell: Cell, suns: list[Cell], regions: Regions) -> list[Cell]:
    """The suns already on the board that break a rule together with a new sun on ``cell``.

    A rule is broken when they share a row, a column or a region, or when they touch.
    """
    row, col = cell
    return [
        sun
        for sun in suns
        if sun[0] == row
        or sun[1] == col
        or regions[sun[0]][sun[1]] == regions[row][col]
        or touches(sun, cell)
    ]


def is_correct(cell: Cell, solution: list[int]) -> bool:
    """Whether the solution has a sun on this cell."""
    row, col = cell
    return solution[row] == col


def is_solved(suns: list[Cell], solution: list[int]) -> bool:
    """The game is solved once every sun of the solution is on the board."""
    return len(suns) == len(solution) and all(is_correct(sun, solution) for sun in suns)


COMBO_MAX_POINTS = 700
TIME_MAX_POINTS = 300


def combo_points(moves: list[bool]) -> int:
    """Combo points of the suns placed so far, in order (``True`` = correct, ``False`` = mistake).

    Each correct sun is worth as much as the current streak: the first is worth 1, the next one
    in a row 2, then 3, and so on. A mistake resets the streak, so the next correct sun is worth
    1 again.
    """
    points = 0
    streak = 0
    for correct in moves:
        if correct:
            streak += 1
            points += streak
        else:
            streak = 0
    return points


def current_streak(moves: list[bool]) -> int:
    """How many correct suns in a row the player has placed since their last mistake."""
    streak = 0
    for correct in reversed(moves):
        if not correct:
            break
        streak += 1
    return streak


def max_combo_points(size: int) -> int:
    """Combo points of a game with no mistakes: 1 + 2 + ... + size."""
    return size * (size + 1) // 2


def score(moves: list[bool], size: int, duration_ms: int) -> int:
    """The final score, from 0 to 1000 (higher is better).

    - Combo, up to 700: ``700 × combo_points / max_combo_points``, so grids of every size can
      reach the same maximum.
    - Time, up to 300: goes down evenly from 300 to 0 over ``size`` minutes (6 minutes for a
      6 × 6 grid), and stays 0 after that.

    For example, a 6 × 6 grid solved in 2 minutes with no mistakes scores 700 + 200 = 900.
    """
    combo = round(COMBO_MAX_POINTS * combo_points(moves) / max_combo_points(size))
    time_limit_ms = size * 60 * 1000
    time = round(TIME_MAX_POINTS * max(0.0, 1 - duration_ms / time_limit_ms))
    return combo + time


def count_solutions(regions: Regions, limit: int = 2) -> int:
    """Count the solutions of a grid with backtracking, stopping at ``limit``.

    A puzzle is valid only when this returns 1. The search fills one row at a time and keeps
    the columns and regions already used, so each row only tries the cells that are still free.
    """
    size = len(regions)
    used_cols: set[int] = set()
    used_regions: set[int] = set()
    found = 0

    def place(row: int, prev_col: int | None) -> None:
        nonlocal found
        if row == size:
            found += 1
            return
        for col in range(size):
            region = regions[row][col]
            if col in used_cols or region in used_regions:
                continue
            # Only the sun on the row above can touch this one: same row and column are
            # already excluded, and rows further up are too far away.
            if prev_col is not None and abs(prev_col - col) <= 1:
                continue
            used_cols.add(col)
            used_regions.add(region)
            place(row + 1, col)
            used_cols.discard(col)
            used_regions.discard(region)
            if found >= limit:
                return

    place(0, None)
    return found


def split_regions(regions: Regions) -> list[int]:
    """The regions whose cells are not all connected to each other (side by side, not
    diagonally), so the region is drawn as several separate pieces."""
    size = len(regions)
    split = []
    for region in sorted({cell for row in regions for cell in row}):
        cells = {(r, c) for r in range(size) for c in range(size) if regions[r][c] == region}
        start = next(iter(cells))
        reached = {start}
        to_visit = [start]
        while to_visit:
            row, col = to_visit.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in cells and neighbor not in reached:
                    reached.add(neighbor)
                    to_visit.append(neighbor)
        if reached != cells:
            split.append(region)
    return split


def validate_puzzle(size: int, regions: Regions, solution: list[int]) -> list[str]:
    """Check that a puzzle is well formed (a square grid of ``size`` connected regions) and has
    exactly one solution, ``solution``.

    Returns the problems found, as messages for the admin; an empty list means valid.
    """
    if size < 4:
        return ["The grid must be at least 4 × 4."]
    if len(regions) != size or any(len(row) != size for row in regions):
        return [f"The regions must be a {size} × {size} grid."]
    if {cell for row in regions for cell in row} != set(range(size)):
        return [f"The grid must have exactly {size} regions, numbered 0 to {size - 1}."]
    split = split_regions(regions)
    if split:
        listed = ", ".join(str(region) for region in split)
        return [f"Every region must be one connected piece; these are split: {listed}."]
    if len(solution) != size or any(not 0 <= col < size for col in solution):
        return [f"The solution must give one column (0 to {size - 1}) for each of the {size} rows."]

    problems = []
    suns: list[Cell] = []
    for row, col in enumerate(solution):
        if conflicts((row, col), suns, regions):
            problems.append(f"The solution breaks a rule on row {row}.")
        suns.append((row, col))
    if problems:
        return problems

    if count_solutions(regions) != 1:
        problems.append("The grid has more than one solution.")
    return problems
