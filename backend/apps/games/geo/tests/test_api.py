import json
from datetime import timedelta

import pytest

from apps.common.time import today_in_romania

from .factories import GeoPuzzleFactory, LocationFactory, RegionFactory

pytestmark = pytest.mark.django_db

GAME_URL = "/api/v1/games/geo/today/"
GUESS_URL = "/api/v1/games/geo/today/guess/"


@pytest.fixture
def puzzle():
    return GeoPuzzleFactory()


@pytest.fixture
def locations(puzzle):
    return [entry.location for entry in puzzle.entries.order_by("position")]


def guess(api_client, round_number, lat, lng, url=GUESS_URL):
    return api_client.post(url, {"round": round_number, "lat": lat, "lng": lng}, format="json")


def text(response) -> str:
    return json.dumps(response.json())


def assert_hidden(response, unguessed):
    """No unguessed location's coordinates or panorama ID appear, except the current panorama."""
    body = text(response)
    current = response.json()["panorama_id"]
    for location in unguessed:
        assert str(location.latitude) not in body
        assert str(location.longitude) not in body
        if location.panorama_id != current:
            assert f'"{location.panorama_id}"' not in body


def test_regions_lists_the_default_region_first(api_client):
    RegionFactory(name="Alba Iulia")

    response = api_client.get("/api/v1/games/geo/regions/")

    assert response.status_code == 200
    assert response.json()[0] == {
        "key": "cluj-napoca",
        "name": "Cluj-Napoca",
        "bounds": {"south": 46.735, "west": 23.53, "north": 46.805, "east": 23.67},
    }
    assert [region["name"] for region in response.json()] == ["Cluj-Napoca", "Alba Iulia"]


def test_open_shows_only_the_first_panorama(api_client, locations):
    response = api_client.get(GAME_URL)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["region"]["key"] == "cluj-napoca"
    assert (data["rounds"], data["current_round"]) == (5, 1)
    assert data["panorama_id"] == locations[0].panorama_id
    assert data["results"] == []
    assert (data["total_score"], data["max_score"]) == (0, 5000)
    assert data["solved"] is None
    assert data["duration_ms"] is None
    assert_hidden(response, locations)


def test_a_guess_reveals_its_location_and_the_next_panorama_only(api_client, locations):
    api_client.get(GAME_URL)

    response = guess(api_client, 1, locations[0].latitude, locations[0].longitude)

    assert response.status_code == 200
    data = response.json()
    assert data["results"] == [
        {
            "round": 1,
            "guess": {"lat": locations[0].latitude, "lng": locations[0].longitude},
            "location": {"lat": locations[0].latitude, "lng": locations[0].longitude},
            "distance_m": 0,
            "score": 1000,
        }
    ]
    assert data["current_round"] == 2
    assert data["panorama_id"] == locations[1].panorama_id
    assert data["total_score"] == 1000
    assert_hidden(response, locations[1:])


def test_a_full_game(api_client, locations):
    for number, location in enumerate(locations, start=1):
        response = guess(api_client, number, location.latitude + 0.009, location.longitude)
        assert response.status_code == 200

    data = response.json()
    assert data["status"] == "completed"
    assert data["current_round"] is None
    assert data["panorama_id"] is None
    assert [row["score"] for row in data["results"]] == [513] * 5
    assert data["total_score"] == 2565
    assert data["solved"] is True
    assert data["duration_ms"] is not None

    again = guess(api_client, 1, locations[0].latitude, locations[0].longitude)
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "already_played"


def test_a_refresh_continues_from_the_current_round(api_client, locations):
    guess(api_client, 1, locations[0].latitude, locations[0].longitude)

    data = api_client.get(GAME_URL).json()

    assert data["current_round"] == 2
    assert len(data["results"]) == 1


@pytest.mark.parametrize(
    ("body", "code", "status"),
    [
        ({"round": 2, "lat": 46.77, "lng": 23.59}, "invalid", 400),
        ({"round": 1, "lat": 44.43, "lng": 26.10}, "invalid", 400),  # Bucharest
        ({"round": 6, "lat": 46.77, "lng": 23.59}, "invalid", 400),
        ({"round": 1, "lat": 95, "lng": 23.59}, "invalid", 400),
        ({"round": 1}, "invalid", 400),
    ],
)
def test_invalid_guesses(api_client, locations, body, code, status):
    response = api_client.post(GUESS_URL, body, format="json")

    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert api_client.get(GAME_URL).json()["current_round"] == 1


def test_guessing_a_round_twice(api_client, locations):
    guess(api_client, 1, 46.77, 23.59)

    response = guess(api_client, 1, 46.77, 23.59)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "already_answered"


def test_another_region_the_same_day(api_client, puzzle):
    other = RegionFactory()
    api_client.get(GAME_URL)

    response = api_client.get(f"{GAME_URL}?region={other.key}")

    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "region_locked",
        "message": "Today's game has already been started in another region.",
        "details": {"region": "cluj-napoca"},
    }


def test_unknown_region(api_client, puzzle):
    response = api_client.get(f"{GAME_URL}?region=atlantis")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "no_region"


def test_no_locations_means_no_puzzle(api_client):
    response = api_client.get(GAME_URL)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "no_puzzle"


def test_today_is_made_on_first_open(api_client):
    LocationFactory.create_batch(10)

    response = api_client.get(GAME_URL)

    assert response.status_code == 200
    assert response.json()["date"] == today_in_romania().isoformat()


def test_past_and_future_days(api_client, puzzle):
    yesterday = (today_in_romania() - timedelta(days=1)).isoformat()
    tomorrow = (today_in_romania() + timedelta(days=1)).isoformat()

    assert api_client.get(f"/api/v1/games/geo/{yesterday}/").json()["error"]["code"] == (
        "archive_unavailable"
    )
    assert api_client.get(f"/api/v1/games/geo/{tomorrow}/").json()["error"]["code"] == ("no_puzzle")


def test_heartbeat_keeps_the_clock_running(api_client, puzzle):
    heartbeat = "/api/v1/results/geo/today/heartbeat/"
    assert api_client.post(heartbeat).status_code == 404  # not started yet

    api_client.get(GAME_URL)

    assert api_client.post(heartbeat).status_code == 204
