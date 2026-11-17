"""Helper tools: AlphabetToNum, Formulas. Pure data/text, no printing."""

from vigenere.cipher import ALPHABET_SIZE


# ---- AlphabetToNum -------------------------------------------------------
def alphabet_table():
    """[('A', 0), ('B', 1), ... ('Z', 25)]"""
    return [(chr(ord("A") + i), i) for i in range(ALPHABET_SIZE)]


def letter_to_number(ch):
    """'c' -> 2. Raises ValueError for anything that is not A-Z / a-z."""
    if len(ch) != 1 or not (ch.isascii() and ch.isalpha()):
        raise ValueError("Enter a single letter from A to Z.")
    return ord(ch.upper()) - ord("A")


def number_to_letter(n):
    """25 -> 'Z'. Wraps around, so -1 also gives 'Z'."""
    return chr(n % ALPHABET_SIZE + ord("A"))


# ---- Formulas ------------------------------------------------------------
FORMULA = "C = (P + K) mod 26"
DECRYPT_FORMULA = "P = (C - K) mod 26"

FORMULA_NOTES = [
    "P = plain letter, C = cipher letter, K = key letter (A=0 ... Z=25).",
    "If P + K goes past 25, it wraps around: (11 + 24) mod 26 = 9 \u2192 J.",
    "If C - K goes below 0, it wraps around too: (9 - 24) mod 26 = 11 \u2192 L.",
    "The key repeats, and only moves forward on letters.",
]