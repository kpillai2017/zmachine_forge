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
import signal

from zforge.common.errors import QuitGame
from zforge.vm.screen.v6 import V6Model
from zforge.vm.screen.base import (KEY_DELETE, KEY_DOWN, KEY_ESCAPE, KEY_F1, KEY_LEFT,
                                   KEY_NEWLINE, KEY_RIGHT, KEY_UP, STYLE_BOLD, STYLE_ITALIC,
                                   STYLE_REVERSE, GridScreen)

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
    """The v5/v7/v8 screen, drawn in a real terminal.

    GridScreen (base.py) keeps a grid of character cells and does all the
    Z-machine rules; this class copies that grid to the terminal and reads keys.
    """
    def __init__(self, stdscr):
        """Set up the terminal: keys arrive one at a time, unechoed; colours if any."""
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
        """The curses attribute (bold, reverse, colour ...) for one grid cell."""
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
        """The curses colour pair for a foreground and background colour.

        curses needs each colour combination registered once, by number, before it
        can be used, and a terminal has only so many; we register them as they turn
        up, and fall back to the default colours (pair 0) if the terminal runs out."""
        key = (fg, bg)
        if key not in self._pairs:
            number = len(self._pairs) + 1
            if number >= curses.COLOR_PAIRS:
                return 0
            curses.init_pair(number, Z_TO_CURSES.get(fg, self._default_colour),
                             Z_TO_CURSES.get(bg, self._default_colour))
            self._pairs[key] = number
        return self._pairs[key]

    _typing = ""          # the line being typed, drawn over the grid (not into it)

    def render(self) -> None:
        """Copy the whole grid to the terminal, then the line being typed."""
        for r, row in enumerate(self.rows):
            for c, cell in enumerate(row):
                if r == self.height - 1 and c == self.width - 1:
                    continue        # writing the bottom-right cell makes curses error
                try:
                    self.stdscr.addstr(r, c, cell.char, self._attribute(cell))
                except curses.error:
                    pass
        # The typed line goes at the CURRENT window's cursor (§8.8.3.5 in v6,
        # the lower window in v5), showing its end if it is too long to fit.
        row, col = self.screen_cursor()
        room = max(self.width - col - 1, 0)
        shown = self._typing[-room:] if room else ""
        try:
            if shown:
                self.stdscr.addstr(row, col, shown)
            self.stdscr.move(row, col + len(shown))
        except curses.error:
            pass
        try:
            curses.curs_set(1 if self.cursor_visible else 0)    # §15 set_cursor -1/-2
        except curses.error:
            pass                    # some terminals cannot hide the cursor
        try:
            self.stdscr.refresh()
        except curses.error:
            pass                    # the terminal has gone (SIGHUP)

    def more_prompt(self) -> None:
        """Show [MORE] on the bottom line and wait for any key (§8.4.1)."""
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
        """Wait for one key from the terminal (dealing with Ctrl-C and resizes)."""
        while True:
            try:
                key = self.stdscr.get_wch()
            except KeyboardInterrupt:
                raise QuitGame("interrupted") from None
            except curses.error:
                continue
            if key == curses.KEY_RESIZE:
                self._terminal_resized()
                continue
            return ord(key) if isinstance(key, str) else key

    def _terminal_resized(self) -> None:
        """The window changed size: resize the screen model (which tells the
        game, §11), then redraw everything from scratch."""
        height, width = self.stdscr.getmaxyx()
        self.resize(width, height)
        self.stdscr.clear()
        self.render()

    def _to_zscii(self, key: int) -> int | None:
        """A curses key as the ZSCII code the game expects, or None if it has none."""
        if key in CURSES_KEY_TO_ZSCII:
            return CURSES_KEY_TO_ZSCII[key]
        if 32 <= key <= 126:
            return key
        return None

    def _input_key(self) -> int:
        """Wait for a key the game can use (others are ignored)."""
        while True:
            code = self._to_zscii(self._raw_key())
            if code is not None:
                return code

    def _input_line(self, max_length: int) -> str:
        """A tiny line editor (Backspace works). The typed text is an overlay
        drawn by render(), never written into the grid: read_line echoes the
        finished line into the right window itself, v5 or v6, and a resize
        in mid-typing just redraws it in its new place."""
        typed: list[str] = []
        try:
            while True:
                self._typing = "".join(typed)
                self.render()
                code = self._to_zscii(self._raw_key())
                if code == KEY_NEWLINE:
                    break
                if code == KEY_DELETE:
                    if typed:
                        typed.pop()
                elif code is not None and 32 <= code <= 126 and len(typed) < max_length:
                    typed.append(chr(code))
        finally:
            self._typing = ""
        return "".join(typed)


class CursesV6Screen(V6Model, CursesScreen):
    """The same, with the §8.8 window model in front of it (v6 stories)."""


def _quit_on_signal(signum, frame):
    """On a hang-up or termination signal, end the game the normal way."""
    raise QuitGame("interrupted")


def run_with_curses(body, version: int = 5):
    """Run body(screen) inside curses.wrapper, so the terminal is ALWAYS
    restored after an exception. Signals too: a closed terminal window
    (SIGHUP) would otherwise kill Python with the terminal still in curses
    mode, and `kill` (SIGTERM), which ncurses cleans up after by itself,
    would skip zforge's own shutdown (a --transcript file is closed there).
    Both become a clean quit instead. The story's version picks the screen
    model: §8.7's two windows, or §8.8's eight."""
    from zforge.common.versions import profile_for
    cls = CursesV6Screen if profile_for(version).windows > 2 else CursesScreen
    caught = [sig for sig in (getattr(signal, "SIGTERM", None), getattr(signal, "SIGHUP", None))
              if sig is not None]
    previous = {sig: signal.signal(sig, _quit_on_signal) for sig in caught}
    try:
        return curses.wrapper(lambda stdscr: body(cls(stdscr)))
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
