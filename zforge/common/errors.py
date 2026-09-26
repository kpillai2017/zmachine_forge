"""Error types. Each carries a user-facing message; the CLI prints it
without a Python traceback (unless --debug)."""
from __future__ import annotations



class ZForgeError(Exception):
    """Base class for all zforge errors."""


class StoryFileError(ZForgeError):
    """The file is not a valid story file (bad header, truncated...)."""


class UnsupportedVersion(StoryFileError):
    """zforge implements version 5 only."""


class ZMachineError(ZForgeError):
    """A fatal run-time error inside the Z-machine (illegal opcode, bad
    address, division by zero...). Spec Appendix A lists such errors."""

    def __init__(self, message: str, pc: int | None = None):
        where = f" at PC=0x{pc:05x}" if pc is not None else ""
        super().__init__(message + where)
        self.pc = pc


class QuitGame(Exception):
    """Raised by @quit to unwind the interpreter loop cleanly (§15 quit)."""


class RestartGame(Exception):
    """Raised by @restart (§15 restart)."""
