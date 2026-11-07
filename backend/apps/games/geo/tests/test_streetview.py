import http.client
import io
import json
import urllib.error
import urllib.parse

import pytest

from apps.games.geo import streetview
from apps.games.geo.exceptions import StreetViewError, TemporaryStreetViewError

GOOGLE_PANORAMA = {
    "status": "OK",
    "copyright": "© Google",
    "pano_id": "abc123",
    "location": {"lat": 46.77, "lng": 23.59},
}


@pytest.fixture
def respond(monkeypatch):
    """Make Google answer with ``body``; returns the list of requested URLs."""
    requested = []

    def install(body=None, error=None):
        def fake_urlopen(url, timeout):
            requested.append(url)
            if error:
                raise error
            return io.BytesIO(json.dumps(body).encode())

        monkeypatch.setattr(streetview.urllib.request, "urlopen", fake_urlopen)
        return requested

    return install


def query(url: str) -> dict:
    return dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))


def test_find_panorama_asks_for_an_outdoor_panorama_near_the_point(respond):
    requested = respond(GOOGLE_PANORAMA)

    panorama = streetview.find_panorama(46.7701, 23.5902, radius_m=100)

    assert panorama == streetview.Panorama("abc123", 46.77, 23.59)
    assert query(requested[0]) == {
        "location": "46.7701,23.5902",
        "radius": "100",
        "source": "outdoor",
        "key": "test-key",
    }


def test_get_panorama_looks_up_the_id(respond):
    requested = respond(GOOGLE_PANORAMA)

    assert streetview.get_panorama("abc123").pano_id == "abc123"
    assert query(requested[0])["pano"] == "abc123"


@pytest.mark.parametrize("status", ["ZERO_RESULTS", "NOT_FOUND"])
def test_no_panorama_there(respond, status):
    respond({"status": status})

    assert streetview.find_panorama(46.77, 23.59) is None


def test_user_photo_spheres_are_ignored(respond):
    respond({**GOOGLE_PANORAMA, "copyright": "© Andrei Teodorovici"})

    assert streetview.find_panorama(46.77, 23.59) is None


@pytest.mark.parametrize("status", ["REQUEST_DENIED", "OVER_QUERY_LIMIT", "UNKNOWN_ERROR"])
def test_a_refused_request_is_an_error(respond, status):
    respond({"status": status, "error_message": "nope"})

    with pytest.raises(StreetViewError, match=status):
        streetview.find_panorama(46.77, 23.59)


def test_network_failure_is_an_error_that_hides_the_key(respond):
    respond(error=urllib.error.URLError("https://maps.googleapis.com/...&key=test-key"))

    with pytest.raises(StreetViewError) as raised:
        streetview.find_panorama(46.77, 23.59)

    assert "test-key" not in str(raised.value)


def test_missing_key_is_an_error_without_a_request(respond, settings):
    requested = respond(GOOGLE_PANORAMA)
    settings.GOOGLE_MAPS_SERVER_KEY = ""

    assert not streetview.is_configured()
    with pytest.raises(StreetViewError):
        streetview.find_panorama(46.77, 23.59)
    assert requested == []


def test_google_unknown_error_is_temporary(respond):
    respond({"status": "UNKNOWN_ERROR"})

    with pytest.raises(TemporaryStreetViewError):
        streetview.find_panorama(46.77, 23.59)


@pytest.mark.parametrize("status", ["REQUEST_DENIED", "OVER_QUERY_LIMIT"])
def test_a_refused_key_is_not_temporary(respond, status):
    respond({"status": status})

    with pytest.raises(StreetViewError) as raised:
        streetview.find_panorama(46.77, 23.59)
    assert not isinstance(raised.value, TemporaryStreetViewError)


@pytest.mark.parametrize(
    "error",
    [
        http.client.RemoteDisconnected("closed"),
        http.client.IncompleteRead(b""),
        ConnectionResetError(),
        TimeoutError(),
    ],
)
def test_a_dropped_connection_is_temporary(respond, error):
    respond(error=error)

    with pytest.raises(TemporaryStreetViewError):
        streetview.find_panorama(46.77, 23.59)
