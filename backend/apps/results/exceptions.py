"""Domain errors raised by the results app."""

from apps.common.exceptions import DomainError


class AlreadyPlayedError(DomainError):
    status_code = 409
    code = "already_played"
    default_message = "This puzzle has already been played."
