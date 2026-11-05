import pytest

from apps.common.exceptions import exception_handler
from apps.games.math import rules
from apps.games.math.exceptions import InvalidNumbersError, InvalidStepError
from apps.games.math.rules import Operator, Step


def test_an_invalid_step_becomes_a_400_in_the_shared_error_format():
    numbers = (1, 2, 3, 25, 50, 100)
    played = [Step(2, Operator.ADD, 1), Step(3, Operator.SUB, 3)]
    with pytest.raises(InvalidStepError) as error:
        rules.replay(numbers, 999, played)

    response = exception_handler(error.value, {})

    assert response.status_code == 400
    assert response.data == {
        "error": {
            "code": "invalid_step",
            "message": "Step 2 can't be played (not_positive).",
            "details": {"step": 1, "reason": rules.NOT_POSITIVE},
        }
    }


def test_invalid_numbers_become_a_400_in_the_shared_error_format():
    with pytest.raises(InvalidNumbersError) as error:
        rules.validate_numbers((25, 25, 1, 2, 3, 4))

    response = exception_handler(error.value, {})

    assert response.status_code == 400
    assert response.data["error"]["code"] == "invalid_puzzle"
    assert response.data["error"]["message"] == "25 can appear at most once."
