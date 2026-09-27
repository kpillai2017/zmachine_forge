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
from zforge.vm.screen.v6 import ATTR_SCROLLING, V6Model


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
        self._last_shown: dict[int, list[str]] = {}    # window -> rows last printed

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
        """Show the upper window's contents if it has any non-blank lines."""
        if self.upper_height == 0:
            return
        self._show_rows(1, self.text_rows()[:self.upper_height])

    def _show_rows(self, window: int, upper: list[str]) -> None:
        """Print a painted window's rows as "| ..." - whenever they changed."""
        if not self.show_upper:
            return
        # Only print if the rows are different from last time and not all blank.
        if upper != self._last_shown.get(window) and any(r.strip() for r in upper):
            if self.column:
                self.out.write("\n")
                self.column = 0
            for r in upper:
                if r.strip():
                    self.out.write(f"| {r.strip()}\n")
            self.out.flush()
        self._last_shown[window] = upper

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
        return self._input_key()

    # The hooks the v6 model's read_line/read_key call (base.py): a stream
    # reads a whole line, from the script or from stdin.
    def _input_line(self, max_length: int) -> str:
        return self._read_raw_line()

    def _input_key(self) -> int:
        if self.script is not None:
            return self.script.next_char()
        line = self.inp.readline()
        if line == "":
            raise QuitGame("end of input")
        self.column = 0
        return ord(line[0]) if line.strip("\r\n") else KEY_NEWLINE


class PlainV6Screen(V6Model, PlainScreen):
    """The same, with the §8.8 window model in front of it (v6 stories).

    A stream has no cursor to move, so it treats windows by what they are
    for (§8.8.3.2: their attributes). A window that SCROLLS holds running
    text, and streams - window 0, by default. A window that does not is
    painted: the status line (window 1), a panel. Its text is kept out of
    the stream, and its rows are shown as "| ..." lines when the game
    switches away from it, whenever they changed - as v5's status line is,
    so a story reads the same on z5 and z6. `--ui curses` draws the real
    layout."""

    _muted = False          # True while a character must not reach the stream

    def _emit(self, ch: str) -> None:
        if not self._muted:
            PlainScreen._emit(self, ch)

    def _write_char(self, w, ch: str) -> None:
        """Every character still lands in its window's grid (get_cursor and
        friends need it); only a painted window's stay out of the stream."""
        muted, self._muted = self._muted, self._muted or not w.has(ATTR_SCROLLING)
        try:
            V6Model._write_char(self, w, ch)
        finally:
            self._muted = muted

    def set_window(self, window: int) -> None:
        leaving = self.current
        V6Model.set_window(self, window)
        if self.current is not leaving and not leaving.has(ATTR_SCROLLING):
            self.show_window(leaving)

    def show_upper_window(self) -> None:
        self.show_window(self.windows[1])

    def show_window(self, w) -> None:
        rows = self.text_rows()[w.top:w.top + w.y_size]
        self._show_rows(w.number, [r[w.left:w.left + w.x_size] for r in rows])

    def read_line(self, max_length: int, initial: str = "") -> str:
        """The v6 model echoes the typed line into the current window. The
        stream has already shown it (a scripted line is echoed by
        _read_raw_line; a typed one by the user's terminal), so the echo
        goes into the grid only."""
        text = V6Model.read_line(self, max_length, initial)   # calls _input_line
        self._muted = False                 # (the echo still reached the transcript)
        return text

    def _input_line(self, max_length: int) -> str:
        line = PlainScreen._input_line(self, max_length)
        self._muted = True                  # until read_line has echoed it
        return line
