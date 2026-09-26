"""§2 Numbers: the Z-machine works in 16-bit words.

Values are STORED unsigned (0..65535). Arithmetic and comparisons treat
them as signed two's complement (-32768..32767). Every conversion in
zforge goes through these two functions so the rule is in one place.
"""

WORD_MASK = 0xFFFF


def to_signed(value: int) -> int:
    """0..65535 -> -32768..32767  (§2.2)."""
    value &= WORD_MASK
    return value - 0x10000 if value & 0x8000 else value


def from_signed(value: int) -> int:
    """Any Python int -> 0..65535, wrapping like 16-bit hardware (§2.3)."""
    return value & WORD_MASK


def truncating_div(a: int, b: int) -> int:
    """Signed division rounding TOWARD ZERO (§2.4.3): -7 / 2 == -3.
    Python's // rounds toward minus infinity, so we cannot use it directly."""
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def truncating_mod(a: int, b: int) -> int:
    """Remainder with the sign of the dividend (§2.4.3): -7 % 2 == -1."""
    return a - b * truncating_div(a, b)
