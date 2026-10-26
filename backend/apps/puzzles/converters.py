"""URL converter for game days: `today` or an ISO date such as `2026-10-26`."""

from datetime import date

from apps.common.time import today_in_romania


class GameDayConverter:
    regex = r"today|\d{4}-\d{2}-\d{2}"

    def to_python(self, value: str) -> date:
        if value == "today":
            return today_in_romania()
        return date.fromisoformat(value)

    def to_url(self, value: date | str) -> str:
        return value if isinstance(value, str) else value.isoformat()
