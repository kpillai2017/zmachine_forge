"""PlainScreen: no cursor control at all - text streams to stdout.

Used when stdout is not a terminal, for --ui plain, and on systems without
curses. The lower window is word-wrapped as it is printed; the upper
window (status lines) is kept in a small grid and shown as "| ... |" lines
as soon as the game switches back to the lower window, whenever it changed.
"""
from __future__ import annotations

import sys

from zforge.common.errors import QuitGame
from zforge.vm.screen.base import KEY_NEWLINE, GridScreen, ScriptInput


class PlainScreen(GridScreen):
    supports_colour = False

    def __init__(self, width: int = 80, height: int = 255, script: list[str] | None = None,
                 out=None, inp=None, show_upper: bool = True):
        super().__init__(width, max(height, 25))
        self.out = out or sys.stdout
        self.inp = inp or sys.stdin
        self.script = ScriptInput(script) if script is not None else None
        self.column = 0
        self.show_upper = show_upper
        self._last_upper: list[str] = []

    # Lower-window text goes straight to stdout via the _emit hook; the grid
    # (which decides where lines wrap) is still kept so get_cursor etc. work.
    def _emit(self, ch: str) -> None:
        self.out.write(ch)
        self.column = 0 if ch == "\n" else self.column + 1

    def flush(self) -> None:
        super().flush()
        self.out.flush()

    def more_prompt(self) -> None:
        pass           # a stream never pauses

    def set_window(self, window: int) -> None:
        """Show the status line as soon as the game has finished drawing it
        (i.e. when it switches back from the upper to the lower window)."""
        leaving_upper = self.window == 1 and window != 1
        super().set_window(window)
        if leaving_upper:
            self.show_upper_window()

    def render(self) -> None:
        """Nothing to draw for a stream (the upper window is shown by
        set_window)."""

    def show_upper_window(self) -> None:
        if not self.show_upper or self.upper_height == 0:
            return
        upper = [r for r in self.text_rows()[:self.upper_height]]
        if upper != self._last_upper and any(r.strip() for r in upper):
            if self.column:
                self.out.write("\n")
                self.column = 0
            for r in upper:
                if r.strip():
                    self.out.write(f"| {r.strip()}\n")
            self.out.flush()
        self._last_upper = upper

    def _read_raw_line(self) -> str:
        if self.script is not None:
            line = self.script.next_line()
            self.out.write(line + "\n")     # echo scripted input
            self.column = 0
            return line
        line = self.inp.readline()
        if line == "":
            raise QuitGame("end of input")
        self.column = 0
        return line.rstrip("\r\n")

    def read_line(self, max_length: int, initial: str = "") -> str:
        self.flush()
        self.render()
        text = self._read_raw_line()[:max_length]
        self.transcript.append(text + "\n")
        self._next_lower_row()          # the echo ended the line: wrap from column 0 again
        self.lines_since_input = 0
        return text

    def read_key(self) -> int:
        self.flush()
        self.render()
        if self.script is not None:
            return self.script.next_char()
        line = self.inp.readline()
        if line == "":
            raise QuitGame("end of input")
        self.column = 0
        return ord(line[0]) if line.strip("\r\n") else KEY_NEWLINE
