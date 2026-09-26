"""CursesScreen: draw the GridScreen in a real terminal with curses.

All of the §8 rules live in GridScreen; this file only:
  * copies the grid to the terminal (render),
  * reads keys and edits the input line on the grid (read_line/read_key),
  * shows [MORE] when a screenful of text has scrolled by,
  * maps Z-machine colours/styles to curses attributes.

Always create it through `run_with_curses` so the terminal is restored on
EVERY exit path (normal quit, fatal error, Ctrl-C) - see proforma §11.
"""
from __future__ import annotations

import curses

from zforge.common.errors import QuitGame
from zforge.vm.screen.v6 import V6Model
from zforge.vm.screen.base import (KEY_DELETE, KEY_DOWN, KEY_ESCAPE, KEY_F1, KEY_LEFT,
                                   KEY_NEWLINE, KEY_RIGHT, KEY_UP, STYLE_BOLD, STYLE_ITALIC,
                                   STYLE_REVERSE, Cell, GridScreen)

# Z-machine colour number -> curses colour (§8.3.1)
Z_TO_CURSES = {2: curses.COLOR_BLACK, 3: curses.COLOR_RED, 4: curses.COLOR_GREEN,
               5: curses.COLOR_YELLOW, 6: curses.COLOR_BLUE, 7: curses.COLOR_MAGENTA,
               8: curses.COLOR_CYAN, 9: curses.COLOR_WHITE}

CURSES_KEY_TO_ZSCII = {
    curses.KEY_UP: KEY_UP, curses.KEY_DOWN: KEY_DOWN,
    curses.KEY_LEFT: KEY_LEFT, curses.KEY_RIGHT: KEY_RIGHT,
    curses.KEY_BACKSPACE: KEY_DELETE, 127: KEY_DELETE, 8: KEY_DELETE,
    10: KEY_NEWLINE, 13: KEY_NEWLINE, curses.KEY_ENTER: KEY_NEWLINE, 27: KEY_ESCAPE,
    **{curses.KEY_F0 + n: KEY_F1 + n - 1 for n in range(1, 13)},
}


class CursesScreen(GridScreen):
    def __init__(self, stdscr):
        self.stdscr = stdscr
        height, width = stdscr.getmaxyx()
        super().__init__(width, height)
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        self.supports_colour = curses.has_colors()
        self._pairs: dict[tuple[int, int], int] = {}
        if self.supports_colour:
            curses.start_color()
            try:
                curses.use_default_colors()
                self._default_colour = -1
            except curses.error:
                self._default_colour = curses.COLOR_BLACK

    # ----------------------------------------------------------- drawing
    def _attribute(self, cell) -> int:
        attr = 0
        if cell.style & STYLE_REVERSE:
            attr |= curses.A_REVERSE
        if cell.style & STYLE_BOLD:
            attr |= curses.A_BOLD
        if cell.style & STYLE_ITALIC:
            attr |= getattr(curses, "A_ITALIC", curses.A_UNDERLINE)
        if self.supports_colour and (cell.fg > 1 or cell.bg > 1):
            attr |= curses.color_pair(self._pair(cell.fg, cell.bg))
        return attr

    def _pair(self, fg: int, bg: int) -> int:
        key = (fg, bg)
        if key not in self._pairs:
            number = len(self._pairs) + 1
            if number >= curses.COLOR_PAIRS:
                return 0
            curses.init_pair(number, Z_TO_CURSES.get(fg, self._default_colour),
                             Z_TO_CURSES.get(bg, self._default_colour))
            self._pairs[key] = number
        return self._pairs[key]

    def render(self) -> None:
        for r, row in enumerate(self.rows):
            for c, cell in enumerate(row):
                if r == self.height - 1 and c == self.width - 1:
                    continue        # writing the bottom-right cell makes curses error
                try:
                    self.stdscr.addstr(r, c, cell.char, self._attribute(cell))
                except curses.error:
                    pass
        row, col = self.upper_cursor if self.window == 1 else self.lower_cursor
        try:
            self.stdscr.move(min(row, self.height - 1), min(col, self.width - 1))
        except curses.error:
            pass
        self.stdscr.refresh()

    def more_prompt(self) -> None:
        self.render()
        try:
            self.stdscr.addstr(self.height - 1, 0, "[MORE]", curses.A_REVERSE)
        except curses.error:
            pass
        self.stdscr.refresh()
        self._raw_key()
        try:
            self.stdscr.addstr(self.height - 1, 0, "      ")
        except curses.error:
            pass

    def close(self, reason: str = "") -> None:
        """Show the final screen and wait, so the ending is not lost when
        curses restores the terminal (Frotz does the same)."""
        self.flush()
        self.render()
        if reason == "interrupted":
            return
        try:
            self.stdscr.addstr(self.height - 1, 0, "[Press any key to exit]", curses.A_REVERSE)
        except curses.error:
            pass
        self.stdscr.refresh()
        try:
            self._raw_key()
        except QuitGame:
            pass

    # ------------------------------------------------------------- input
    def _raw_key(self) -> int:
        while True:
            try:
                key = self.stdscr.get_wch()
            except KeyboardInterrupt:
                raise QuitGame("interrupted") from None
            except curses.error:
                continue
            if key == curses.KEY_RESIZE:
                continue            # simple approach: keep the original grid size
            return ord(key) if isinstance(key, str) else key

    def _to_zscii(self, key: int) -> int | None:
        if key in CURSES_KEY_TO_ZSCII:
            return CURSES_KEY_TO_ZSCII[key]
        if 32 <= key <= 126:
            return key
        return None

    def _input_key(self) -> int:
        while True:
            code = self._to_zscii(self._raw_key())
            if code is not None:
                return code

    def _input_line(self, max_length: int) -> str:
        """A tiny line editor drawn straight onto the grid (Backspace works)."""
        typed: list[str] = []
        start_row, start_col = self.lower_cursor
        while True:
            self.render()
            code = self._to_zscii(self._raw_key())
            if code == KEY_NEWLINE:
                break
            if code == KEY_DELETE and typed:
                typed.pop()
                row, col = self.lower_cursor
                if col > 0:
                    self.rows[row][col - 1] = Cell(" ")
                    self.lower_cursor = (row, col - 1)
            elif code is not None and 32 <= code <= 126 and len(typed) < max_length:
                typed.append(chr(code))
                row, col = self.lower_cursor
                if col < self.width - 1:
                    self.rows[row][col] = Cell(chr(code), self.style)
                    self.lower_cursor = (row, col + 1)
        # GridScreen.read_line re-echoes the text; rewind to where typing began
        self.lower_cursor = (start_row, start_col)
        for c in range(start_col, self.width):
            self.rows[start_row][c] = Cell(" ")
        return "".join(typed)


class CursesV6Screen(V6Model, CursesScreen):
    """The same, with the §8.8 window model in front of it (v6 stories)."""


def run_with_curses(body, version: int = 5):
    """Run body(screen) inside curses.wrapper, so the terminal is ALWAYS
    restored - even after an exception. The story's version picks the
    screen model: §8.7's two windows, or §8.8's eight."""
    from zforge.common.versions import profile_for
    cls = CursesV6Screen if profile_for(version).windows > 2 else CursesScreen
    return curses.wrapper(lambda stdscr: body(cls(stdscr)))
