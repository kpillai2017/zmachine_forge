"""§2: 16-bit signed arithmetic."""
from zforge.common.numbers import from_signed, to_signed, truncating_div, truncating_mod


def test_signed_round_trip():
    for v in (-32768, -1, 0, 1, 32767):
        assert to_signed(from_signed(v)) == v
    assert to_signed(0xFFFF) == -1 and from_signed(65536 + 5) == 5


def test_division_truncates_toward_zero():
    assert truncating_div(-7, 2) == -3 and truncating_div(7, -2) == -3
    assert truncating_mod(-7, 2) == -1 and truncating_mod(7, -2) == 1
