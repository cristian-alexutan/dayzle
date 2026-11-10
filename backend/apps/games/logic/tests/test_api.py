import pytest

from apps.games.logic import rules

from .factories import LogicPuzzleFactory

pytestmark = pytest.mark.django_db

GAME_URL = "/api/v1/games/logic/today/"
CELL_URL = "/api/v1/games/logic/today/cell/"
CLEAR_URL = "/api/v1/games/logic/today/clear/"
SOLUTION_CELLS = list(enumerate(rules.DEMO_SOLUTION))


@pytest.fixture(autouse=True)
def todays_puzzle():
    LogicPuzzleFactory()


def set_cell(api_client, row, col, content="sun"):
    return api_client.post(CELL_URL, {"row": row, "col": col, "content": content}, format="json")


def test_board_shows_the_grid_without_the_solution(api_client):
    response = api_client.get(GAME_URL)

    assert response.status_code == 200
    data = response.data
    assert data["status"] == "in_progress"
    assert data["size"] == 6
    assert data["regions"] == rules.DEMO_REGIONS
    assert data["suns"] == [] and data["marks"] == []
    assert data["mistakes"] == 0
    assert data["score"] is None
    assert data["elapsed_ms"] == 0
    assert "solution" not in data


def test_accepted_and_rejected_suns(api_client):
    accepted = set_cell(api_client, 0, 2).data
    rejected = set_cell(api_client, 0, 3).data

    assert accepted["rejected"] is False
    assert rejected["rejected"] is True
    assert rejected["conflicts"] == [[0, 2]]
    assert rejected["game"]["suns"] == [[0, 2]]
    assert rejected["game"]["mistakes"] == 1


def test_marks_are_saved_and_restored(api_client):
    set_cell(api_client, 1, 1, "mark")
    set_cell(api_client, 2, 2, "mark")

    assert api_client.get(GAME_URL).data["marks"] == [[1, 1], [2, 2]]


def test_a_cell_can_be_emptied(api_client):
    set_cell(api_client, 0, 0)

    response = set_cell(api_client, 0, 0, "empty")

    assert response.data["game"]["suns"] == []


def test_finishing_returns_the_score_and_duration_but_never_the_solution(api_client):
    response = None
    for row, col in SOLUTION_CELLS:
        response = set_cell(api_client, row, col)

    game = response.data["game"]
    assert game["status"] == "completed"
    assert game["solved"] is True
    assert 900 <= game["score"] <= 1000
    assert game["duration_ms"] is not None
    assert game["elapsed_ms"] == game["duration_ms"]
    assert "solution" not in game
    assert "solution" not in api_client.get(GAME_URL).data


def test_clear_empties_the_board(api_client):
    set_cell(api_client, 0, 2)
    set_cell(api_client, 3, 3, "mark")

    response = api_client.post(CLEAR_URL)

    assert response.status_code == 200
    assert response.data["suns"] == [] and response.data["marks"] == []


@pytest.mark.parametrize(
    "body",
    [
        {"row": 6, "col": 0, "content": "sun"},
        {"row": -1, "col": 0, "content": "sun"},
        {"row": 0, "col": 0, "content": "moon"},
        {"row": 0, "col": 0},
        {},
    ],
)
def test_invalid_requests_return_invalid(api_client, body):
    response = api_client.post(CELL_URL, body, format="json")

    assert response.status_code == 400
    assert response.data["error"]["code"] == "invalid"


def test_playing_after_finishing_is_already_played(api_client):
    for row, col in SOLUTION_CELLS:
        set_cell(api_client, row, col)

    response = set_cell(api_client, 0, 0, "mark")

    assert response.status_code == 409
    assert response.data["error"]["code"] == "already_played"


def test_each_guest_has_their_own_game(api_client, client):
    set_cell(api_client, 0, 2)

    assert client.get(GAME_URL).json()["suns"] == []
