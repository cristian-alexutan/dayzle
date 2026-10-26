from datetime import UTC, date, datetime
from unittest import mock

import pytest

from apps.common.time import today_in_romania


@pytest.mark.parametrize(
    ("utc_now", "expected"),
    [
        # Summer (UTC+3): midnight in Romania is 21:00 UTC.
        (datetime(2026, 7, 1, 20, 59, tzinfo=UTC), date(2026, 7, 1)),
        (datetime(2026, 7, 1, 21, 0, tzinfo=UTC), date(2026, 7, 2)),
        # Winter (UTC+2): midnight in Romania is 22:00 UTC.
        (datetime(2026, 12, 1, 21, 59, tzinfo=UTC), date(2026, 12, 1)),
        (datetime(2026, 12, 1, 22, 0, tzinfo=UTC), date(2026, 12, 2)),
    ],
)
def test_today_in_romania_switches_at_romanian_midnight(utc_now, expected):
    with mock.patch("django.utils.timezone.now", return_value=utc_now):
        assert today_in_romania() == expected
