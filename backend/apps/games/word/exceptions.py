"""Domain errors raised by the Word game app."""

from apps.common.exceptions import DomainError


class InvalidGuessError(DomainError):
    status_code = 400
    code = "invalid"
    default_message = "A guess must have 5 letters of the Romanian alphabet."


class NotAWordError(DomainError):
    status_code = 400
    code = "not_a_word"
    default_message = "This word is not in the word list."
