"""Game-day helpers. The daily reset happens at midnight in Romania."""

from datetime import date
from zoneinfo import ZoneInfo

from django.utils import timezone

ROMANIA_TZ = ZoneInfo("Europe/Bucharest")


def today_in_romania() -> date:
    """Return the current game day. No other code should compute "today"."""
    return timezone.localdate(timezone=ROMANIA_TZ)
