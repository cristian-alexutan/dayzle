import pytest

from apps.games.logic import rules

from .factories import LogicPuzzleFactory

pytestmark = pytest.mark.django_db

GAME_URL = "/api/v1/games/logic/today/"
PLACE_URL = "/api/v1/games/logic/today/place/"
MARKS_URL = "/api/v1/games/logic/today/marks/"
SOLUTION_CELLS = list(enumerate(rules.DEMO_SOLUTION))


@pytest.fixture(autouse=True)
def todays_puzzle():
    LogicPuzzleFactory()


def place(api_client, row, col):
    return api_client.post(PLACE_URL, {"row": row, "col": col}, format="json")


def test_board_shows_the_grid_without_the_solution(api_client):
    response = api_client.get(GAME_URL)

    assert response.status_code == 200
    data = response.data
    assert data["status"] == "in_progress"
    assert data["size"] == 6
    assert data["regions"] == rules.DEMO_REGIONS
    assert data["suns"] == [] and data["marks"] == []
    assert data["mistakes"] == 0 and data["streak"] == 0
    assert data["score"] is None
    assert data["elapsed_ms"] == 0
    assert data["solution"] is None


def test_placing_a_sun_never_reveals_the_solution(api_client):
    response = place(api_client, 0, 0)

    assert response.status_code == 200
    assert "solution" not in response.data
    assert response.data["game"]["solution"] is None


def test_correct_and_wrong_suns(api_client):
    correct = place(api_client, 0, 2).data
    wrong = place(api_client, 0, 3).data

    assert correct["correct"] is True
    assert wrong["correct"] is False
    assert wrong["conflicts"] == [[0, 2]]
    assert wrong["game"]["suns"] == [[0, 2]]
    assert wrong["game"]["mistakes"] == 1
    assert wrong["game"]["streak"] == 0


def test_the_streak_grows_with_correct_suns(api_client):
    place(api_client, 0, 2)
    response = place(api_client, 1, 0)

    assert response.data["game"]["streak"] == 2


def test_finishing_returns_the_score_and_duration(api_client):
    response = None
    for row, col in SOLUTION_CELLS:
        response = place(api_client, row, col)

    game = response.data["game"]
    assert game["status"] == "completed"
    assert game["solved"] is True
    assert 900 <= game["score"] <= 1000
    assert game["duration_ms"] is not None
    assert game["elapsed_ms"] == game["duration_ms"]
    assert game["solution"] == rules.DEMO_SOLUTION
    assert api_client.get(GAME_URL).data["solution"] == rules.DEMO_SOLUTION


def test_marks_are_saved_and_restored(api_client):
    api_client.post(MARKS_URL, {"marks": [[1, 1], [2, 2]]}, format="json")

    assert api_client.get(GAME_URL).data["marks"] == [[1, 1], [2, 2]]


@pytest.mark.parametrize(
    ("url", "body"),
    [
        (PLACE_URL, {"row": 6, "col": 0}),
        (PLACE_URL, {"row": -1, "col": 0}),
        (PLACE_URL, {}),
        (MARKS_URL, {"marks": [[0, 9]]}),
        (MARKS_URL, {"marks": [[0]]}),
    ],
)
def test_invalid_requests_return_invalid(api_client, url, body):
    response = api_client.post(url, body, format="json")

    assert response.status_code == 400
    assert response.data["error"]["code"] == "invalid"


def test_playing_after_finishing_is_already_played(api_client):
    for row, col in SOLUTION_CELLS:
        place(api_client, row, col)

    response = place(api_client, 0, 0)

    assert response.status_code == 409
    assert response.data["error"]["code"] == "already_played"


def test_each_guest_has_their_own_game(api_client, client):
    place(api_client, 0, 2)

    assert client.get(GAME_URL).json()["suns"] == []
