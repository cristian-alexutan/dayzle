"""Domain errors raised by the Logic game app."""

from apps.common.exceptions import DomainError


class InvalidCellError(DomainError):
    status_code = 400
    code = "invalid"
    default_message = "This cell is outside the grid."
