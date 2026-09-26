"""§15 routine calls and returns (§6.4). All call_* forms share
vm.call_routine; the *n forms discard the result (no store byte)."""
from __future__ import annotations

from zforge.common.errors import ZMachineError


def _call(vm, routine, args):
    vm.call_routine(routine, list(args), vm.current.store)


def op_call_1s(vm, routine):
    """§15 call_1s (1OP:136): call routine with no arguments, store result."""
    _call(vm, routine, [])


def op_call_1n(vm, routine):
    """§15 call_1n (1OP:143 in v5): call, discard result."""
    _call(vm, routine, [])


def op_call_2s(vm, routine, arg1):
    """§15 call_2s (2OP:25): call with one argument, store result."""
    _call(vm, routine, [arg1])


def op_call_2n(vm, routine, arg1):
    """§15 call_2n (2OP:26): call with one argument, discard result."""
    _call(vm, routine, [arg1])


def op_call_vs(vm, routine, *args):
    """§15 call_vs (VAR:224): call with up to 3 arguments, store result."""
    _call(vm, routine, args)


def op_call_vn(vm, routine, *args):
    """§15 call_vn (VAR:249): call with up to 3 arguments, discard result."""
    _call(vm, routine, args)


def op_call_vs2(vm, routine, *args):
    """§15 call_vs2 (VAR:236): up to 7 arguments (two type bytes, §4.4.3.1)."""
    _call(vm, routine, args)


def op_call_vn2(vm, routine, *args):
    """§15 call_vn2 (VAR:250): up to 7 arguments, discard result."""
    _call(vm, routine, args)


def op_ret(vm, value):
    """§15 ret (1OP:139): return value."""
    vm.ret(value)


def op_rtrue(vm):
    """§15 rtrue (0OP:176): return 1."""
    vm.ret(1)


def op_rfalse(vm):
    """§15 rfalse (0OP:177): return 0."""
    vm.ret(0)


def op_ret_popped(vm):
    """§15 ret_popped (0OP:184): pop the stack and return that value."""
    vm.ret(vm.frame.pop())


def op_catch(vm):
    """§15 catch (0OP:185 in v5): store a 'stack frame' value identifying
    the current routine call. We use the frame depth."""
    vm.store_result(len(vm.frames))


def op_throw(vm, value, frame_id):
    """§15 throw (2OP:28): unwind to the frame that executed the matching
    catch, then return `value` as if from that routine."""
    if not 1 <= frame_id <= len(vm.frames):
        raise ZMachineError(f"throw to a frame that no longer exists ({frame_id})",
                            vm.current.address)
    del vm.frames[frame_id:]
    vm.ret(value)
