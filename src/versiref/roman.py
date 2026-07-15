"""Conversion between integers and Roman numerals.

Bible chapter numbers never exceed 200, so only the letters C, L, X, V, and I
are needed, but the functions handle the full M/D/C/L/X/V/I alphabet.
"""

_ROMAN_VALUES = [
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
]

_LETTER_VALUES = {
    "M": 1000,
    "D": 500,
    "C": 100,
    "L": 50,
    "X": 10,
    "V": 5,
    "I": 1,
}


def int_to_roman(n: int) -> str:
    """Convert a positive integer to an uppercase Roman numeral.

    Uses the modern subtractive style, e.g. 4 -> "IV", 44 -> "XLIV".

    Args:
        n: The number to convert. Must be positive.

    Raises:
        ValueError: If n is not positive.

    Returns:
        The Roman numeral as an uppercase string.

    """
    if n <= 0:
        raise ValueError(f"Cannot represent {n} as a Roman numeral")
    result = []
    for value, letters in _ROMAN_VALUES:
        count, n = divmod(n, value)
        result.append(letters * count)
    return "".join(result)


def roman_to_int(s: str) -> int:
    """Convert a Roman numeral to an integer.

    Case-insensitive. A letter smaller than the one following it is
    subtracted, so both modern subtractive forms ("IV") and additive forms
    ("IIII") are accepted. Malformed sequences are not rejected.

    Args:
        s: The Roman numeral to convert.

    Raises:
        ValueError: If s is empty or contains a non-Roman-numeral character.

    Returns:
        The numeral's integer value.

    """
    if not s:
        raise ValueError("Empty string is not a Roman numeral")
    total = 0
    previous = 0
    for letter in reversed(s.upper()):
        if letter not in _LETTER_VALUES:
            raise ValueError(f"Invalid Roman numeral character: {letter!r}")
        value = _LETTER_VALUES[letter]
        if value < previous:
            total -= value
        else:
            total += value
            previous = value
    return total
