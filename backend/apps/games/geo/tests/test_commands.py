from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.common.time import today_in_romania
from apps.games.geo import services, streetview
from apps.games.geo.models import GeoPuzzle, Location
from apps.puzzles.models import Game
from apps.puzzles.tests.factories import DailyPuzzleFactory

from .factories import GeoPuzzleFactory, LocationFactory

pytestmark = pytest.mark.django_db


def run(*args) -> tuple[str, str]:
    out, err = StringIO(), StringIO()
    call_command(*args, stdout=out, stderr=err)
    return out.getvalue(), err.getvalue()


def test_generate_locations(monkeypatch):
    found = iter([streetview.Panorama("a", 46.77, 23.59), streetview.Panorama("b", 46.78, 23.6)])
    monkeypatch.setattr(streetview, "find_panorama", lambda *args: next(found, None))

    out, err = run("generate_locations", "--count", "3", "--seed", "1")

    assert "cluj-napoca: added 2 location(s)" in out
    assert "Only 2 of 3 found" in err
    assert Location.objects.count() == 2


def test_generate_locations_needs_a_key(settings):
    settings.GOOGLE_MAPS_SERVER_KEY = ""

    with pytest.raises(CommandError, match="GOOGLE_MAPS_SERVER_KEY"):
        run("generate_locations")


def test_generate_locations_unknown_region():
    with pytest.raises(CommandError, match="no such region"):
        run("generate_locations", "--region", "atlantis")


def test_check_panoramas_checks_the_coming_days_only(monkeypatch):
    soon = GeoPuzzleFactory()
    later = GeoPuzzleFactory(
        daily_puzzle=DailyPuzzleFactory(game=Game.GEO, date=today_in_romania() + timedelta(days=30))
    )
    checked = []
    monkeypatch.setattr(streetview, "get_panorama", lambda pano_id: checked.append(pano_id))

    out, err = run("check_panoramas", "--days", "7")

    assert sorted(checked) == sorted(soon.locations.values_list("panorama_id", flat=True))
    assert not set(checked) & set(later.locations.values_list("panorama_id", flat=True))
    assert "Checked 5 location(s)." in out
    assert err.count("Removed by Google") == 5


def test_check_panoramas_all(monkeypatch):
    LocationFactory.create_batch(3)
    LocationFactory(is_active=False)
    monkeypatch.setattr(
        streetview, "get_panorama", lambda pano_id: streetview.Panorama(pano_id, 46.77, 23.59)
    )

    out, _ = run("check_panoramas", "--all")

    assert "Checked 3 location(s)." in out


def test_prepare_geo_days():
    LocationFactory.create_batch(40)

    out, err = run("prepare_geo_days", "--days", "3")

    assert GeoPuzzle.objects.count() == 3
    assert err == ""
    # Running again makes nothing new.
    run("prepare_geo_days", "--days", "3")
    assert GeoPuzzle.objects.count() == 3


def test_prepare_geo_days_reports_a_small_bank():
    _, err = run("prepare_geo_days", "--days", "1")

    assert "too few locations" in err


def test_seed_dev_makes_geo_games(settings, monkeypatch):
    settings.DEBUG = True
    bank = LocationFactory.build_batch(services.SEED_BANK_SIZE)
    found = iter(streetview.Panorama(loc.panorama_id, loc.latitude, loc.longitude) for loc in bank)
    monkeypatch.setattr(streetview, "find_panorama", lambda *args: next(found, None))

    out, _ = run("seed_dev", "--days", "3")

    assert "geo: created 3 puzzle(s)" in out
    assert GeoPuzzle.objects.count() == 3


def test_seed_dev_fills_in_a_geo_day_after_a_failed_run(settings, monkeypatch):
    """The first run can't reach Google; the next one makes the days it left empty."""
    settings.DEBUG = True

    def google_down(*args):
        raise streetview.TemporaryStreetViewError("Street View returned UNKNOWN_ERROR")

    monkeypatch.setattr(streetview, "find_panorama", google_down)
    run("seed_dev", "--days", "2")
    assert not GeoPuzzle.objects.exists()

    bank = LocationFactory.build_batch(services.SEED_BANK_SIZE)
    found = iter(streetview.Panorama(loc.panorama_id, loc.latitude, loc.longitude) for loc in bank)
    monkeypatch.setattr(streetview, "find_panorama", lambda *args: next(found, None))
    out, _ = run("seed_dev", "--days", "2")

    assert "geo: created 2 puzzle(s)" in out
    assert GeoPuzzle.objects.count() == 2
