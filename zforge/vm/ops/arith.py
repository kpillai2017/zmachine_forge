"""§15 arithmetic and bitwise opcodes. Operands arrive UNSIGNED (0..65535);
signed maths goes through to_signed / from_signed (§2)."""
from __future__ import annotations

from zforge.common.errors import ZMachineError
from zforge.common.numbers import from_signed, to_signed, truncating_div, truncating_mod


def op_add(vm, a, b):
    """§15 add (2OP:20): a + b, signed 16-bit, wrapping."""
    vm.store_result(from_signed(to_signed(a) + to_signed(b)))


def op_sub(vm, a, b):
    """§15 sub (2OP:21): a - b."""
    vm.store_result(from_signed(to_signed(a) - to_signed(b)))


def op_mul(vm, a, b):
    """§15 mul (2OP:22): a * b."""
    vm.store_result(from_signed(to_signed(a) * to_signed(b)))


def op_div(vm, a, b):
    """§15 div (2OP:23): signed division, rounding toward zero (§2.4.3).
    Division by zero is a fatal error (§2.4.2)."""
    if to_signed(b) == 0:
        raise ZMachineError("Division by zero (§15 div)", vm.current.address)
    vm.store_result(from_signed(truncating_div(to_signed(a), to_signed(b))))


def op_mod(vm, a, b):
    """§15 mod (2OP:24): remainder after truncating division; takes the sign
    of the dividend: -13 % 5 = -3, 13 % -5 = 3."""
    if to_signed(b) == 0:
        raise ZMachineError("Division by zero (§15 mod)", vm.current.address)
    vm.store_result(from_signed(truncating_mod(to_signed(a), to_signed(b))))


def op_or(vm, a, b):
    """§15 or (2OP:8): bitwise or."""
    vm.store_result(a | b)


def op_and(vm, a, b):
    """§15 and (2OP:9): bitwise and."""
    vm.store_result(a & b)


def op_not(vm, value):
    """§15 not (VAR:248 in v5): bitwise not."""
    vm.store_result(~value & 0xFFFF)


def op_log_shift(vm, number, places):
    """§15 log_shift (EXT:2): logical shift; positive = left, negative = right
    (zeros shifted in)."""
    places = to_signed(places)
    vm.store_result((number << places) & 0xFFFF if places >= 0 else number >> -places)


def op_art_shift(vm, number, places):
    """§15 art_shift (EXT:3): arithmetic shift; right shifts keep the sign."""
    places = to_signed(places)
    value = to_signed(number)
    vm.store_result(from_signed(value << places if places >= 0 else value >> -places))
