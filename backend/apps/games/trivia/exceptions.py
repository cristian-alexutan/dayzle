"""Domain errors raised by the Trivia game app."""

from apps.common.exceptions import DomainError


class InvalidAnswerError(DomainError):
    status_code = 400
    code = "invalid"
    default_message = "The question is not in today's quiz or the choice is not one of its options."


class OutOfOrderError(DomainError):
    status_code = 400
    code = "out_of_order"
    default_message = "Questions must be answered in order."


class AlreadyAnsweredError(DomainError):
    status_code = 409
    code = "already_answered"
    default_message = "This question has already been answered."
