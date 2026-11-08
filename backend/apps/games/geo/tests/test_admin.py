import pytest
from django.urls import reverse

from apps.games.geo import streetview
from apps.games.geo.models import Location

from .factories import GeoPuzzleFactory, LocationFactory, cluj

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("name", ["games_geo_region_changelist", "games_geo_location_changelist"])
def test_admin_pages_load(admin_client, name):
    GeoPuzzleFactory()

    assert admin_client.get(reverse(f"admin:{name}")).status_code == 200


def test_nothing_can_be_added_or_deleted(admin_client):
    location = LocationFactory()

    assert admin_client.get(reverse("admin:games_geo_location_add")).status_code == 403
    assert admin_client.get(reverse("admin:games_geo_region_add")).status_code == 403
    delete = reverse("admin:games_geo_location_delete", args=[location.pk])
    assert admin_client.get(delete).status_code == 403


def test_a_location_is_read_only_except_active(admin_client):
    location = LocationFactory()
    url = reverse("admin:games_geo_location_change", args=[location.pk])

    response = admin_client.post(url, {"is_active": "", "latitude": "1", "panorama_id": "x"})

    assert response.status_code == 302
    location.refresh_from_db()
    assert not location.is_active
    assert location.panorama_id.startswith("pano-")
    assert location.latitude != 1


def test_region_scoring_can_be_tuned_but_not_its_bounds(admin_client):
    region = cluj()
    url = reverse("admin:games_geo_region_change", args=[region.pk])

    admin_client.post(
        url,
        {"is_active": "on", "score_scale_m": "2000", "min_spacing_m": "800", "south": "0"},
    )

    region.refresh_from_db()
    assert (region.score_scale_m, region.min_spacing_m, region.south) == (2000, 800, 46.735)


def run_action(admin_client, action, locations):
    return admin_client.post(
        reverse("admin:games_geo_location_changelist"),
        {"action": action, "_selected_action": [location.pk for location in locations]},
        follow=True,
    )


def test_deactivate_action(admin_client):
    locations = LocationFactory.create_batch(2)

    run_action(admin_client, "deactivate", locations)

    assert not Location.objects.filter(is_active=True).exists()


def test_recheck_action_deactivates_removed_panoramas(admin_client, monkeypatch):
    kept, removed = LocationFactory(), LocationFactory()
    answers = {kept.panorama_id: streetview.Panorama(kept.panorama_id, 46.75, 23.6)}
    monkeypatch.setattr(streetview, "get_panorama", answers.get)

    response = run_action(admin_client, "recheck", [kept, removed])

    assert removed.panorama_id in response.content.decode()
    assert Location.objects.get(pk=kept.pk).is_active
    assert not Location.objects.get(pk=removed.pk).is_active


def test_recheck_action_without_a_key_shows_an_error(admin_client, settings):
    settings.GOOGLE_MAPS_SERVER_KEY = ""
    location = LocationFactory()

    response = run_action(admin_client, "recheck", [location])

    assert "GOOGLE_MAPS_SERVER_KEY is not set" in response.content.decode()
