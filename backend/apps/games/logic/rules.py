"""Rules of the Logic game (Sunspots), with no Django code.

The grid is ``size`` × ``size`` cells, divided into ``size`` colored regions. The player places one
sun in every row, every column and every region, and no two suns may touch, not even diagonally.

A cell is a ``(row, col)`` pair, counted from 0. ``regions[row][col]`` is the region number of a
cell (0 to size - 1), and ``solution[row]`` is the column of the sun on that row.
"""

Cell = tuple[int, int]
Regions = list[list[int]]

# Grid sizes a puzzle may have. Above 9 × 9 the solver gets slow when an admin saves a puzzle.
MIN_SIZE = 4
MAX_SIZE = 9

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


# The score starts at 1000 and goes down evenly to 0 over 2 minutes per row (12 minutes for a
# 6 × 6 grid). Each rejected sun costs 50 more points.
MAX_SCORE = 1000
TIME_LIMIT_PER_ROW_MS = 2 * 60 * 1000
MISTAKE_PENALTY = 50


def is_full(suns: list[Cell], size: int) -> bool:
    """Every row has its sun. Each sun was only accepted if it broke no rule, and every puzzle
    has exactly one solution, so a full board is that solution."""
    return len(suns) == size


def score(size: int, duration_ms: int, mistakes: int) -> int:
    """The final score, from 0 to 1000 (higher is better):
    ``max(0, round(1000 × (1 − duration / limit)) − 50 × mistakes)``, with ``limit`` = 2 minutes
    per row.

    For example, a 6 × 6 grid solved in 3 minutes with 1 mistake scores 750 − 50 = 700.
    """
    limit_ms = size * TIME_LIMIT_PER_ROW_MS
    time_points = round(MAX_SCORE * (1 - duration_ms / limit_ms))
    return max(0, time_points - MISTAKE_PENALTY * mistakes)


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
    if not MIN_SIZE <= size <= MAX_SIZE:
        return [f"The grid must be from {MIN_SIZE} × {MIN_SIZE} to {MAX_SIZE} × {MAX_SIZE}."]
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
