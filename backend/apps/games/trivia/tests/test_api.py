import pytest

from apps.games.trivia.models import Choice

from .factories import TriviaPuzzleFactory

pytestmark = pytest.mark.django_db

GAME_URL = "/api/v1/games/trivia/today/"
ANSWER_URL = "/api/v1/games/trivia/today/answer/"


@pytest.fixture(autouse=True)
def quiz():
    return TriviaPuzzleFactory()


def correct(question_id: int) -> int:
    return Choice.objects.get(question_id=question_id, is_correct=True).pk


def wrong(question_id: int) -> int:
    return Choice.objects.filter(question_id=question_id, is_correct=False).first().pk


def test_quiz_never_says_which_choice_is_correct(api_client):
    response = api_client.get(GAME_URL)

    assert response.status_code == 200
    assert response.data["status"] == "in_progress"
    assert len(response.data["questions"]) == 5
    assert set(response.data["questions"][0]) == {"id", "category", "text", "choices"}
    assert set(response.data["questions"][0]["choices"][0]) == {"id", "text"}
    assert "is_correct" not in response.content.decode()
    assert response.data["answers"] == []
    assert response.data["score"] is None
    assert response.data["max_score"] == 5


def test_answer_says_if_it_was_right_and_reveals_the_correct_choice(api_client):
    first = api_client.get(GAME_URL).data["questions"][0]["id"]

    response = api_client.post(
        ANSWER_URL, {"question": first, "choice": wrong(first)}, format="json"
    )

    assert response.status_code == 200
    assert response.data["answers"] == [
        {
            "question": first,
            "choice": wrong(first),
            "correct_choice": correct(first),
            "is_correct": False,
        }
    ]
    assert response.data["score"] is None


def test_the_fifth_answer_returns_the_final_score(api_client):
    questions = [q["id"] for q in api_client.get(GAME_URL).data["questions"]]
    for question in questions[:-1]:
        api_client.post(ANSWER_URL, {"question": question, "choice": correct(question)})

    response = api_client.post(
        ANSWER_URL, {"question": questions[-1], "choice": wrong(questions[-1])}, format="json"
    )

    assert response.data["status"] == "completed"
    assert response.data["score"] == 4
    assert response.data["solved"] is False
    assert response.data["duration_ms"] is not None
    assert api_client.get(GAME_URL).data["score"] == 4


def test_answering_twice_is_already_answered(api_client):
    first = api_client.get(GAME_URL).data["questions"][0]["id"]
    api_client.post(ANSWER_URL, {"question": first, "choice": wrong(first)}, format="json")

    response = api_client.post(
        ANSWER_URL, {"question": first, "choice": correct(first)}, format="json"
    )

    assert response.status_code == 409
    assert response.data["error"]["code"] == "already_answered"


def test_skipping_a_question_is_out_of_order(api_client):
    second = api_client.get(GAME_URL).data["questions"][1]["id"]

    response = api_client.post(
        ANSWER_URL, {"question": second, "choice": correct(second)}, format="json"
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "out_of_order"


@pytest.mark.parametrize("body", [{}, {"question": "x", "choice": 1}, {"question": 0, "choice": 0}])
def test_bad_input_is_invalid(api_client, body):
    response = api_client.post(ANSWER_URL, body, format="json")

    assert response.status_code == 400
    assert response.data["error"]["code"] == "invalid"


def test_answering_after_finishing_is_already_played(api_client):
    questions = [q["id"] for q in api_client.get(GAME_URL).data["questions"]]
    for question in questions:
        api_client.post(ANSWER_URL, {"question": question, "choice": correct(question)})

    response = api_client.post(
        ANSWER_URL, {"question": questions[0], "choice": correct(questions[0])}, format="json"
    )

    assert response.status_code == 409
    assert response.data["error"]["code"] == "already_played"


def test_no_quiz_is_no_puzzle(api_client, quiz):
    quiz.daily_puzzle.delete()

    response = api_client.get(GAME_URL)

    assert response.status_code == 404
    assert response.data["error"]["code"] == "no_puzzle"
