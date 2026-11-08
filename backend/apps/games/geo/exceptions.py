"""Domain errors raised by the GeoGuesser game app."""

from apps.common.exceptions import DomainError


class UnknownRegionError(DomainError):
    status_code = 404
    code = "no_region"
    default_message = "There is no such region."


class InvalidGuessError(DomainError):
    status_code = 400
    code = "invalid"
    default_message = "Guess the current round, with a point inside the region."


class AlreadyAnsweredError(DomainError):
    status_code = 409
    code = "already_answered"
    default_message = "This round has already been guessed."


class RegionLockedError(DomainError):
    status_code = 409
    code = "region_locked"
    default_message = "Today's game has already been started in another region."


class StreetViewError(DomainError):
    """Google's Street View Metadata API couldn't be used. Never raised while playing."""

    status_code = 503
    code = "streetview_unavailable"
    default_message = "Street View could not be reached."


class TemporaryStreetViewError(StreetViewError):
    """A failure worth retrying: a network problem or Google's own ``UNKNOWN_ERROR``."""
