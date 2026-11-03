"""Rules of the Word game that need no database: normalization, coloring and scoring."""

import unicodedata
from collections import Counter

WORD_LENGTH = 5
MAX_ATTEMPTS = 6
# The 26 Latin letters plus ă, â, î, ș, ț. Each diacritic is a separate letter.
ALPHABET = frozenset("abcdefghijklmnopqrstuvwxyzăâîșț")

CORRECT = "correct"  # right letter, right place (green)
PRESENT = "present"  # in the word, elsewhere (yellow)
ABSENT = "absent"  # not in the word, or no copies left (gray)


def normalize(text: str) -> str:
    """Lowercase, compose accents and turn the old cedilla ş/ţ into ș/ț."""
    text = unicodedata.normalize("NFC", text.strip()).lower()
    return text.replace("ş", "ș").replace("ţ", "ț")


def is_well_formed(word: str) -> bool:
    """Whether a normalized word has the right length and only letters of the alphabet."""
    return len(word) == WORD_LENGTH and set(word) <= ALPHABET


def color_guess(guess: str, answer: str) -> list[str]:
    """Color each letter of the guess, following the Wordle rule for repeated letters.

    Exact matches are green first; then a letter is yellow only as many times as it still
    appears in the answer, and the rest are gray.
    """
    colors = [ABSENT] * len(guess)
    unmatched = Counter()
    for index, (guessed, expected) in enumerate(zip(guess, answer, strict=True)):
        if guessed == expected:
            colors[index] = CORRECT
        else:
            unmatched[expected] += 1
    for index, guessed in enumerate(guess):
        if colors[index] != CORRECT and unmatched[guessed] > 0:
            colors[index] = PRESENT
            unmatched[guessed] -= 1
    return colors


def score(*, solved: bool, attempts: int) -> int:
    """7 minus the number of attempts when solved (6 on the first try, 1 on the sixth), else 0."""
    return MAX_ATTEMPTS + 1 - attempts if solved else 0
