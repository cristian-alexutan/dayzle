"""Domain errors raised by the puzzles app."""

from apps.common.exceptions import DomainError


class NoPuzzleError(DomainError):
    status_code = 404
    code = "no_puzzle"
    default_message = "There is no puzzle for this game on this day."


class ArchiveUnavailableError(DomainError):
    status_code = 403
    code = "archive_unavailable"
    default_message = "Past puzzles are not available yet."
