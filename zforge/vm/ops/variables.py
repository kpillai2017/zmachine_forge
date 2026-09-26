"""§15 variable opcodes. Several take a variable NUMBER as an operand -
an INDIRECT reference (§6.3.4): for variable 0 they touch the top of the
stack in place rather than pushing/popping."""
from __future__ import annotations

from zforge.common.numbers import from_signed, to_signed


def op_inc(vm, variable):
    """§15 inc (1OP:133): variable += 1 (signed)."""
    vm.write_variable_in_place(variable, to_signed(vm.read_variable_in_place(variable)) + 1)


def op_dec(vm, variable):
    """§15 dec (1OP:134): variable -= 1 (signed)."""
    vm.write_variable_in_place(variable, to_signed(vm.read_variable_in_place(variable)) - 1)


def op_inc_chk(vm, variable, value):
    """§15 inc_chk (2OP:5): increment variable, branch if now > value."""
    new = to_signed(vm.read_variable_in_place(variable)) + 1
    vm.write_variable_in_place(variable, new)
    vm.branch(to_signed(from_signed(new)) > to_signed(value))


def op_dec_chk(vm, variable, value):
    """§15 dec_chk (2OP:4): decrement variable, branch if now < value."""
    new = to_signed(vm.read_variable_in_place(variable)) - 1
    vm.write_variable_in_place(variable, new)
    vm.branch(to_signed(from_signed(new)) < to_signed(value))


def op_load(vm, variable):
    """§15 load (1OP:142): store the value of `variable` (no pop for 0)."""
    vm.store_result(vm.read_variable_in_place(variable))


def op_store(vm, variable, value):
    """§15 store (2OP:13): set `variable` to value (for 0: replace top)."""
    vm.write_variable_in_place(variable, value)


def op_push(vm, value):
    """§15 push (VAR:232): push value onto the stack."""
    vm.frame.push(value)


def op_pull(vm, variable):
    """§15 pull (VAR:233): pop the stack into `variable`; for variable 0
    the popped value then REPLACES the new top (§6.3.4)."""
    value = vm.frame.pop()
    vm.write_variable_in_place(variable, value)
