"""Problem messages, in Inform 7's style.

Inform 7 reports mistakes as 'problems' that quote what you wrote:

    Problem. You wrote 'The cloak is on the lamp' (line 12), but the lamp
    is not a supporter, so nothing can be put on it.

zforge collects them all (so one run shows every problem), and the driver
raises a single I7Problem at the end if there were any."""

from __future__ import annotations

from dataclasses import dataclass, field

from zforge.common.errors import ZForgeError


@dataclass(frozen=True)
class Location:
    line: int
    column: int = 1


class I7Problem(ZForgeError):
    """One or more problems in an I7-lite source."""


@dataclass
class Problems:
    filename: str
    messages: list[str] = field(default_factory=list)

    def problem(self, where: Location, wrote: str, why: str) -> None:
        wrote = " ".join(wrote.split())
        if len(wrote) > 70:
            wrote = wrote[:67] + "..."
        self.messages.append(
            f"{self.filename}:{where.line}: Problem. You wrote '{wrote}', but {why}")

    def unsupported(self, where: Location, wrote: str, what: str) -> None:
        self.problem(where, wrote,
                     f"{what} is not part of I7-lite (see docs/I7_LITE.md).")

    def raise_if_any(self) -> None:
        if self.messages:
            n = len(self.messages)
            head = "1 problem" if n == 1 else f"{n} problems"
            raise I7Problem(f"{head}:\n" + "\n".join(self.messages))
