"""§15 comparison and jump opcodes. Each 'branch' opcode calls vm.branch(cond);
the Branch data decoded in §4.7 decides where (if anywhere) to go."""
from __future__ import annotations

from zforge.common.numbers import to_signed


def op_je(vm, a, *others):
    """§15 je (2OP:1): branch if a equals ANY of the 1-3 other operands.
    (Variable form lets je take up to 4 operands.)"""
    vm.branch(any(a == b for b in others))


def op_jl(vm, a, b):
    """§15 jl (2OP:2): branch if a < b (signed)."""
    vm.branch(to_signed(a) < to_signed(b))


def op_jg(vm, a, b):
    """§15 jg (2OP:3): branch if a > b (signed)."""
    vm.branch(to_signed(a) > to_signed(b))


def op_jz(vm, a):
    """§15 jz (1OP:128): branch if a == 0."""
    vm.branch(a == 0)


def op_test(vm, bitmap, flags):
    """§15 test (2OP:7): branch if every bit set in flags is set in bitmap."""
    vm.branch(bitmap & flags == flags)


def op_jump(vm, offset):
    """§15 jump (1OP:140): unconditional jump. NOT a branch instruction: the
    operand is a signed offset; target = address after instruction + offset - 2."""
    vm.pc = vm.current.next_address + to_signed(offset) - 2


def op_check_arg_count(vm, number):
    """§15 check_arg_count (VAR:255): branch if argument `number` (1-based)
    was supplied to the current routine."""
    vm.branch(number <= vm.frame.arg_count)


def op_piracy(vm):
    """§15 piracy (0OP:191): branch if the game disc is 'genuine' -
    interpreters should always branch."""
    vm.branch(True)
