"""Error types. Each carries a user-facing message; the CLI prints it
without a Python traceback (unless --debug)."""
from __future__ import annotations



class ZForgeError(Exception):
    """Base class for all zforge errors."""


class StoryFileError(ZForgeError):
    """The file is not a valid story file (bad header, truncated...)."""


class UnsupportedVersion(StoryFileError):
    """A story-file version zforge does not run (see common/versions.py)."""


class LayoutError(ZForgeError, ValueError):
    """The story cannot be laid out for this version: too big (§1.1.4), or
    an address a packed address cannot reach (§1.2.3)."""


class UnsupportedTarget(ZForgeError):
    """A --target / zforge.toml / ZFORGE_TARGET value zforge cannot build."""


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
