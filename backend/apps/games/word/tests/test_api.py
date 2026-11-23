import pytest

from .factories import WordFactory, WordPuzzleFactory

pytestmark = pytest.mark.django_db

GAME_URL = "/api/v1/games/word/today/"
GUESS_URL = "/api/v1/games/word/today/guess/"


@pytest.fixture(autouse=True)
def todays_word():
    WordFactory(text="tunel", is_answer=False)
    WordPuzzleFactory(answer=WordFactory(text="carte"))


def test_board_hides_the_answer_while_in_progress(api_client):
    response = api_client.get(GAME_URL)

    assert response.status_code == 200
    assert response.data["status"] == "in_progress"
    assert response.data["guesses"] == []
    assert response.data["answer"] is None
    assert response.data["score"] is None
    assert "carte" not in response.content.decode()


def test_guess_returns_colors_without_the_answer(api_client):
    response = api_client.post(GUESS_URL, {"guess": "tunel"}, format="json")

    assert response.status_code == 200
    assert response.data["guesses"][0]["colors"] == [
        "present",
        "absent",
        "absent",
        "present",
        "absent",
    ]
    assert "carte" not in response.content.decode()


def test_finishing_reveals_answer_and_score(api_client):
    api_client.post(GUESS_URL, {"guess": "tunel"}, format="json")

    response = api_client.post(GUESS_URL, {"guess": "carte"}, format="json")

    assert response.data["status"] == "completed"
    assert response.data["answer"] == "carte"
    assert response.data["solved"] is True
    assert response.data["score"] == 5
    assert api_client.get(GAME_URL).data["answer"] == "carte"


@pytest.mark.parametrize(
    ("body", "code"),
    [({"guess": "cart"}, "invalid"), ({"guess": "zzzzz"}, "not_a_word"), ({}, "invalid")],
)
def test_rejected_guesses_return_an_error(api_client, body, code):
    response = api_client.post(GUESS_URL, body, format="json")

    assert response.status_code == 400
    assert response.data["error"]["code"] == code


def test_guessing_after_finishing_is_already_played(api_client):
    api_client.post(GUESS_URL, {"guess": "carte"}, format="json")

    response = api_client.post(GUESS_URL, {"guess": "tunel"}, format="json")

    assert response.status_code == 409
    assert response.data["error"]["code"] == "already_played"


def test_each_guest_has_their_own_game(api_client, client):
    api_client.post(GUESS_URL, {"guess": "carte"}, format="json")

    other = client.get(GAME_URL)

    assert other.json()["status"] == "in_progress"


HINT_URL = "/api/v1/games/word/today/hint/"


def test_a_new_board_has_no_hints_and_shows_the_penalty(api_client):
    response = api_client.get(GAME_URL)

    assert response.data["hints"] == []
    assert response.data["hint_penalty"] == 2


def test_hint_returns_the_board_with_one_letter_of_the_word(api_client):
    response = api_client.post(HINT_URL)

    assert response.status_code == 200
    assert response.data["status"] == "in_progress"
    assert response.data["answer"] is None
    assert len(response.data["hints"]) == 1
    assert response.data["hints"][0] in "carte"
    assert api_client.get(GAME_URL).data["hints"] == response.data["hints"]


def test_hint_when_every_letter_is_known_is_nothing_to_hint(api_client):
    for _ in range(5):
        api_client.post(HINT_URL)

    response = api_client.post(HINT_URL)

    assert response.status_code == 409
    assert response.data["error"]["code"] == "nothing_to_hint"
