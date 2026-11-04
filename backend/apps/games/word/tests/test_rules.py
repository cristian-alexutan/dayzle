import pytest

from apps.games.word import rules
from apps.games.word.rules import ABSENT as A
from apps.games.word.rules import CORRECT as C
from apps.games.word.rules import PRESENT as P


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("CÂINE", "câine"),
        ("  carte ", "carte"),
        ("şanţ", "șanț"),  # old cedilla forms
        ("ŞARPE", "șarpe"),
        ("câine", "câine"),  # "â" typed as a + combining circumflex
    ],
)
def test_normalize(raw, expected):
    assert rules.normalize(raw) == expected


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        ("câine", True),  # diacritics count as one letter each
        ("cărți", True),
        ("cart", False),
        ("cartea", False),
        ("cart3", False),
        ("müsli", False),
    ],
)
def test_is_well_formed(word, expected):
    assert rules.is_well_formed(word) is expected


@pytest.mark.parametrize(
    ("guess", "answer", "expected"),
    [
        ("carte", "carte", [C, C, C, C, C]),
        ("tunel", "carte", [P, A, A, P, A]),
        # Only one "a" in the answer: the exact match is green, the other "a" is gray.
        ("barza", "carte", [A, C, C, A, A]),
        # Three "e" guessed, two in the answer: one exact match, one yellow, the last one gray.
        ("eeeaa", "verde", [P, C, A, A, A]),
        ("leneș", "verde", [A, C, A, P, A]),
        # a, ă and â are different letters.
        ("pâine", "păine", [C, A, C, C, C]),
        ("sărat", "sarat", [C, A, C, C, C]),
    ],
)
def test_color_guess(guess, answer, expected):
    assert rules.color_guess(guess, answer) == expected


@pytest.mark.parametrize(
    ("solved", "attempts", "expected"),
    [(True, 1, 6), (True, 3, 4), (True, 6, 1), (False, 6, 0)],
)
def test_score(solved, attempts, expected):
    assert rules.score(solved=solved, attempts=attempts) == expected
