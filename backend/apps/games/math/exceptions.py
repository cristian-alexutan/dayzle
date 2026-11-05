"""Domain errors raised by the Math game app."""

from apps.common.exceptions import DomainError


class InvalidNumbersError(DomainError):
    """A set of starting numbers or a target that breaks the puzzle rules."""

    status_code = 400
    code = "invalid_puzzle"
    default_message = "The puzzle's numbers or target break the rules."


class InvalidStepError(DomainError):
    """A step that can't be played.

    ``details`` says which step failed (``step``, 0-based) and why (``reason``). The step is
    None when a single operation is checked on its own, before it is part of a replay.
    """

    status_code = 400
    code = "invalid_step"
    default_message = "This step can't be played."

    def __init__(self, reason: str, index: int | None = None) -> None:
        self.reason = reason
        self.index = index
        message = None if index is None else f"Step {index + 1} can't be played ({reason})."
        super().__init__(message, details={"step": index, "reason": reason})


class NoStepsError(DomainError):
    status_code = 400
    code = "invalid"
    default_message = "Make at least one step before submitting."
