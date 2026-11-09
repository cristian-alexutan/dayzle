"""Fixtures for the GeoGuesser tests. Google is never called: every request is mocked."""

import pytest

from apps.games.geo import streetview


@pytest.fixture(autouse=True)
def no_network(settings, monkeypatch):
    """A fake key, and an error if any code path reaches Google for real."""
    settings.GOOGLE_MAPS_SERVER_KEY = "test-key"

    def refuse(*args, **kwargs):
        raise AssertionError("Tests must not call Google; mock apps.games.geo.streetview.")

    monkeypatch.setattr(streetview.urllib.request, "urlopen", refuse)
