"""§5 Routines and §6.3-6.4 the stack and call frames.

Each routine call gets a Frame holding its local variables (1..15), its own
slice of the evaluation stack, where to return to, and where to store the
result. Keeping the evaluation stack per frame makes the Quetzal "Stks"
chunk and @throw simple to implement.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from zforge.common.errors import ZMachineError

MAX_LOCALS = 15
STACK_LIMIT = 16384      # a generous guard against runaway recursion


@dataclass
class Frame:
    return_pc: int                 # where execution resumes after return
    locals: list[int]              # locals[0] is local variable 1
    store_var: int | None          # variable to receive the result; None = discard
    arg_count: int                 # number of arguments supplied (§15 check_arg_count)
    stack: list[int] = field(default_factory=list)   # this frame's evaluation stack

    def push(self, value: int) -> None:
        if len(self.stack) >= STACK_LIMIT:
            raise ZMachineError("Stack overflow")
        self.stack.append(value & 0xFFFF)

    def pop(self) -> int:
        if not self.stack:
            raise ZMachineError("Stack underflow (§6.3.2)")
        return self.stack.pop()

    def peek(self) -> int:
        if not self.stack:
            raise ZMachineError("Stack underflow (§6.3.2)")
        return self.stack[-1]

    def poke(self, value: int) -> None:
        """Replace the top of the stack IN PLACE (§6.3.4 indirect references)."""
        if not self.stack:
            raise ZMachineError("Stack underflow (§6.3.2)")
        self.stack[-1] = value & 0xFFFF

    def copy(self) -> "Frame":
        return Frame(self.return_pc, list(self.locals), self.store_var,
                     self.arg_count, list(self.stack))
