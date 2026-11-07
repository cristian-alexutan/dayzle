"""Client for Google's Street View Metadata API, the only place this game talks to Google.

Used when locations are generated and rechecked, never while someone plays. Metadata requests
are free. The key is ``GOOGLE_MAPS_SERVER_KEY``, restricted to the Street View Static API.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from django.conf import settings

from .exceptions import StreetViewError

METADATA_URL = "https://maps.googleapis.com/maps/api/streetview/metadata"
TIMEOUT_S = 10
# Statuses meaning "no panorama here": anything else that isn't OK is a problem with the request.
NOT_FOUND_STATUSES = {"ZERO_RESULTS", "NOT_FOUND"}


@dataclass(frozen=True)
class Panorama:
    pano_id: str
    lat: float
    lng: float


def is_configured() -> bool:
    return bool(settings.GOOGLE_MAPS_SERVER_KEY)


def _fetch(params: dict) -> dict:
    if not is_configured():
        raise StreetViewError("GOOGLE_MAPS_SERVER_KEY is not set.")
    query = urllib.parse.urlencode({**params, "key": settings.GOOGLE_MAPS_SERVER_KEY})
    try:
        with urllib.request.urlopen(f"{METADATA_URL}?{query}", timeout=TIMEOUT_S) as response:
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        # Never include the URL: it contains the key.
        raise StreetViewError(f"Street View request failed: {type(error).__name__}") from None


def _parse(data: dict) -> Panorama | None:
    status = data.get("status")
    if status in NOT_FOUND_STATUSES:
        return None
    if status != "OK":
        message = data.get("error_message") or "no details"
        raise StreetViewError(f"Street View returned {status}: {message}")
    # Only Google's own imagery: user photo spheres can be indoors, moved or removed at will.
    if "Google" not in data.get("copyright", ""):
        return None
    location = data.get("location") or {}
    try:
        return Panorama(str(data["pano_id"]), float(location["lat"]), float(location["lng"]))
    except KeyError, TypeError, ValueError:
        return None


def find_panorama(lat: float, lng: float, radius_m: int = 100) -> Panorama | None:
    """The nearest outdoor Google panorama within ``radius_m`` of a point, if there is one."""
    return _parse(_fetch({"location": f"{lat},{lng}", "radius": radius_m, "source": "outdoor"}))


def get_panorama(pano_id: str) -> Panorama | None:
    """A known panorama with its current coordinates, or None if Google no longer has it."""
    return _parse(_fetch({"pano": pano_id}))
