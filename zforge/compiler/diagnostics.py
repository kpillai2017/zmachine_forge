"""Compiler diagnostics: "file:line:col: error: message" plus the source
line and a caret under the offending column. Errors are COLLECTED so one
run reports as many problems as possible."""
from __future__ import annotations

from dataclasses import dataclass, field

from zforge.common.errors import ZForgeError


@dataclass(frozen=True)
class Location:
    line: int
    column: int


@dataclass
class Diagnostic:
    location: Location
    message: str

    def format(self, filename: str, source_lines: list[str]) -> str:
        loc = self.location
        text = source_lines[loc.line - 1] if 0 < loc.line <= len(source_lines) else ""
        caret = " " * (loc.column - 1) + "^"
        return f"{filename}:{loc.line}:{loc.column}: error: {self.message}\n    {text}\n    {caret}"


@dataclass
class Diagnostics:
    filename: str
    source: str
    items: list[Diagnostic] = field(default_factory=list)

    def error(self, location: Location, message: str) -> None:
        self.items.append(Diagnostic(location, message))

    def __bool__(self) -> bool:
        return bool(self.items)

    def report(self) -> str:
        lines = self.source.splitlines()
        ordered = sorted(self.items, key=lambda d: (d.location.line, d.location.column))
        return "\n".join(d.format(self.filename, lines) for d in ordered)


class CompileError(ZForgeError):
    """Raised at the end of a stage when diagnostics were recorded."""

    def __init__(self, diagnostics: Diagnostics):
        super().__init__(diagnostics.report())
        self.diagnostics = diagnostics
