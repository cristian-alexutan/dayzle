import pytest

from .factories import MathPuzzleFactory

pytestmark = pytest.mark.django_db

GAME_URL = "/api/v1/games/math/today/"
PROGRESS_URL = "/api/v1/games/math/today/progress/"
SUBMIT_URL = "/api/v1/games/math/today/submit/"

SECRETS = ("solution", "min_operations", "difficulty")
RESULTS = ("final_result", "distance", "operations", "solved", "score", "duration_ms")


def body(*steps: tuple[int, str, int]) -> dict:
    return {"steps": [{"left": left, "op": op, "right": right} for left, op, right in steps]}


SOLVED = body((100, "*", 2), (50, "+", 3), (200, "+", 53))


@pytest.fixture(autouse=True)
def todays_puzzle():
    MathPuzzleFactory()  # 253 from 1, 2, 3, 25, 50, 100


def test_board_shows_the_puzzle_without_secrets(api_client):
    response = api_client.get(GAME_URL)

    assert response.status_code == 200
    assert response.data["status"] == "in_progress"
    assert response.data["target"] == 253
    assert response.data["numbers"] == [1, 2, 3, 25, 50, 100]
    assert response.data["max_steps"] == 5
    assert response.data["steps"] == []
    assert all(response.data[key] is None for key in SECRETS + RESULTS)


def test_progress_returns_the_replayed_steps_without_secrets(api_client):
    # The browser's own "result" is ignored: the server computes every result itself.
    sent = {"steps": [{"left": 100, "op": "*", "right": 2, "result": 999}]}

    response = api_client.post(PROGRESS_URL, sent, format="json")

    assert response.status_code == 200
    assert response.data["steps"] == [{"left": 100, "op": "*", "right": 2, "result": 200}]
    assert all(response.data[key] is None for key in SECRETS + RESULTS)
    assert api_client.get(GAME_URL).data["steps"] == response.data["steps"]


def test_submit_reveals_the_result_and_the_solution(api_client):
    response = api_client.post(SUBMIT_URL, SOLVED, format="json")

    assert response.status_code == 200
    assert response.data["status"] == "completed"
    assert response.data["final_result"] == 253
    assert response.data["distance"] == 0
    assert response.data["operations"] == 3
    assert response.data["solved"] is True
    assert response.data["score"] == 1000
    assert response.data["duration_ms"] is not None
    assert response.data["solution"][-1] == {"left": 200, "op": "+", "right": 53, "result": 253}
    assert response.data["min_operations"] == 3
    assert response.data["difficulty"] == "easy"
    assert api_client.get(GAME_URL).data["solution"] == response.data["solution"]


def test_progress_that_reaches_the_target_finishes_the_game(api_client):
    response = api_client.post(PROGRESS_URL, SOLVED, format="json")

    assert response.status_code == 200
    assert response.data["status"] == "completed"
    assert response.data["solved"] is True
    assert response.data["score"] == 1000
    assert response.data["solution"] is not None
    assert api_client.post(SUBMIT_URL, SOLVED, format="json").status_code == 409


def test_an_inexact_submit_is_scored_by_distance(api_client):
    response = api_client.post(SUBMIT_URL, body((100, "*", 2), (200, "+", 50)), format="json")

    assert response.data["solved"] is False
    assert response.data["final_result"] == 250
    assert response.data["score"] == 840


@pytest.mark.parametrize(
    ("url", "sent"),
    [
        (SUBMIT_URL, {"steps": []}),
        (SUBMIT_URL, {}),
        (PROGRESS_URL, {"steps": [{"left": 100, "op": "^", "right": 2}]}),
        (PROGRESS_URL, {"steps": [{"left": "a", "op": "+", "right": 2}]}),
    ],
)
def test_malformed_requests_are_invalid(api_client, url, sent):
    response = api_client.post(url, sent, format="json")

    assert response.status_code == 400
    assert response.data["error"]["code"] == "invalid"


@pytest.mark.parametrize("url", [PROGRESS_URL, SUBMIT_URL])
def test_a_broken_rule_is_an_invalid_step_that_does_not_end_the_game(api_client, url):
    response = api_client.post(url, body((100, "*", 2), (200, "/", 3)), format="json")

    assert response.status_code == 400
    assert response.data["error"]["code"] == "invalid_step"
    assert response.data["error"]["details"] == {"step": 1, "reason": "not_whole"}
    assert api_client.get(GAME_URL).data["status"] == "in_progress"


@pytest.mark.parametrize("url", [PROGRESS_URL, SUBMIT_URL])
def test_playing_after_finishing_is_already_played(api_client, url):
    api_client.post(SUBMIT_URL, SOLVED, format="json")

    response = api_client.post(url, body((100, "+", 1)), format="json")

    assert response.status_code == 409
    assert response.data["error"]["code"] == "already_played"


def test_each_guest_has_their_own_game(api_client, client):
    api_client.post(SUBMIT_URL, SOLVED, format="json")

    other = client.get(GAME_URL).json()

    assert other["status"] == "in_progress"
    assert other["solution"] is None
