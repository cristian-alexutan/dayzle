"""Domain errors raised by the Logic game app."""

from apps.common.exceptions import DomainError


class InvalidCellError(DomainError):
    status_code = 400
    code = "invalid"
    default_message = "This cell is outside the grid."


class NothingToHintError(DomainError):
    status_code = 409
    code = "nothing_to_hint"
    default_message = "Every row already has its sun on the board or a hint."
