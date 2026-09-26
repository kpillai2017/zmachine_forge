"""§8 The version-5 screen model, as a grid of character cells.

Version 5 has two windows (§8.7):

    +--------------------------------+  row 0
    | window 1 (upper)               |  fixed, unbuffered, no scrolling;
    |                                |  the game moves the cursor itself
    +--------------------------------+  row = upper_height
    | window 0 (lower)               |  buffered (word-wrapped), scrolls
    |                                |  up; the game just prints into it
    +--------------------------------+  row = height - 1

GridScreen keeps the WHOLE picture as rows of Cell(char, style, fg, bg).
Renderers (curses, tests) only have to draw the grid; all the rules of
§8 live here, in one place.

Text styles (§8.7.1.1, set_text_style): 0 roman, 1 reverse, 2 bold,
4 italic, 8 fixed-pitch - they combine.
Colours (§8.3.1): 0 current, 1 default, 2 black, 3 red, 4 green, 5 yellow,
6 blue, 7 magenta, 8 cyan, 9 white.
"""
from __future__ import annotations

from dataclasses import dataclass

from zforge.common.errors import QuitGame

STYLE_ROMAN, STYLE_REVERSE, STYLE_BOLD, STYLE_ITALIC, STYLE_FIXED = 0, 1, 2, 4, 8
COLOUR_CURRENT, COLOUR_DEFAULT = 0, 1

# ZSCII input codes for special keys (§3.8.2.4 - §3.8.2.7)
KEY_DELETE, KEY_NEWLINE, KEY_ESCAPE = 8, 13, 27
KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT = 129, 130, 131, 132
KEY_F1 = 133          # F1..F12 = 133..144


@dataclass(frozen=True)
class Cell:
    char: str = " "
    style: int = 0
    fg: int = COLOUR_DEFAULT
    bg: int = COLOUR_DEFAULT


BLANK = Cell()


class ScriptInput:
    """Scripted keyboard input: a list of lines (used by tests and --script).
    When it runs out, the game is ended cleanly (QuitGame)."""

    def __init__(self, lines: list[str]):
        self.lines = list(lines)
        self.pending: str | None = None

    def next_line(self) -> str:
        if self.pending is not None:
            line, self.pending = self.pending, None
            return line
        if not self.lines:
            raise QuitGame("scripted input exhausted")
        return self.lines.pop(0)

    def next_char(self) -> int:
        if self.pending is None:
            self.pending = self.next_line() + "\n"
        ch, self.pending = self.pending[0], self.pending[1:] or None
        return KEY_NEWLINE if ch == "\n" else ord(ch)


class GridScreen:
    """The §8 model. Subclasses supply input (_input_line/_input_key) and may
    override render() / more_prompt()."""

    supports_colour = True
    on_resize = None        # the machine's hook: on_resize(width, height)

    def __init__(self, width: int = 80, height: int = 24):
        self.width, self.height = width, height
        self.rows = [[BLANK] * width for _ in range(height)]
        self.upper_height = 0
        self.window = 0
        self.upper_cursor = (0, 0)            # (row, col), 0-based
        self.lower_cursor = (0, 0)            # v5: lower window starts top-left
        self.style = STYLE_ROMAN
        self.fg, self.bg = COLOUR_DEFAULT, COLOUR_DEFAULT
        self.buffering = True                 # §15 buffer_mode (lower window only)
        self.word_buffer: list[str] = []
        self.lines_since_input = 0
        self.font = 1
        self.transcript: list[str] = []       # everything shown in window 0 (+input)

    # ---------------------------------------------------------------- resize
    def resize(self, width: int, height: int) -> None:
        """The terminal changed size. The upper window keeps its rows from
        the top (it is the status line), the lower window keeps its NEWEST
        lines - the ones up to the cursor - and the game is told (§11)."""
        width, height = max(width, 1), max(height, 1)
        if (width, height) == (self.width, self.height):
            return
        def fit(row):
            return (row + [BLANK] * width)[:width]
        upper = min(self.upper_height, height)
        cursor_row = max(self.lower_cursor[0], self.upper_height)
        lower_rows = self.rows[self.upper_height:cursor_row + 1]
        kept = lower_rows[-(height - upper):] if height > upper else []
        self.rows = ([fit(r) for r in self.rows[:upper]] + [fit(r) for r in kept]
                     + [[BLANK] * width for _ in range(height - upper - len(kept))])
        self.lower_cursor = (min(upper + max(len(kept) - 1, 0), height - 1),
                             min(self.lower_cursor[1], width - 1))
        self.upper_cursor = (min(self.upper_cursor[0], max(upper - 1, 0)),
                             min(self.upper_cursor[1], width - 1))
        self.upper_height = upper
        self.width, self.height = width, height
        self.lines_since_input = 0
        if self.on_resize:
            self.on_resize(width, height)

    def screen_cursor(self) -> tuple[int, int]:
        """Where the terminal's cursor goes: the current window's cursor."""
        return self.upper_cursor if self.window == 1 else self.lower_cursor

    cursor_visible = True      # v6's set_cursor -1 hides it (§15)

    # ---------------------------------------------------------------- output
    def print(self, text: str) -> None:
        for ch in text:
            if self.window == 1:
                self._put_upper(ch)
            elif self.buffering:
                self._buffer_lower(ch)
            else:
                self._put_lower(ch)

    def _buffer_lower(self, ch: str) -> None:
        """Word-wrap: collect a word, and flush it at a space or newline."""
        if ch in (" ", "\n"):
            self.flush()
            self._put_lower(ch)
        else:
            self.word_buffer.append(ch)

    def flush(self) -> None:
        if not self.word_buffer:
            return
        word = "".join(self.word_buffer)
        self.word_buffer = []
        col = self.lower_cursor[1]
        if col > 0 and col + len(word) > self.width:
            self._put_lower("\n")
        for ch in word:
            self._put_lower(ch)

    def _put_lower(self, ch: str) -> None:
        row, col = self.lower_cursor
        self.transcript.append(ch)
        if ch == "\n":
            self._lower_newline()
            return
        if col >= self.width:
            self._lower_newline(wrapped=True)
            row, col = self.lower_cursor
        if ch == " " and col == 0 and self._just_wrapped:
            self._just_wrapped = False
            return                      # don't start a wrapped line with a space
        self.rows[row][col] = Cell(ch, self.style, self.fg, self.bg)
        self.lower_cursor = (row, col + 1)
        self._just_wrapped = False
        self._emit(ch)

    def _emit(self, ch: str) -> None:
        """Hook: a character (or "\n") has just appeared in the lower window.
        PlainScreen streams it to stdout; other screens draw the grid instead."""

    _just_wrapped = False

    def _lower_newline(self, wrapped: bool = False) -> None:
        self._emit("\n")
        self._next_lower_row()
        self._just_wrapped = wrapped
        self.lines_since_input += 1
        lower_lines = self.height - self.upper_height
        if self.lines_since_input >= lower_lines - 1:
            self.more_prompt()
            self.lines_since_input = 0

    def _next_lower_row(self) -> None:
        """Move the lower-window cursor to the start of the next row,
        scrolling at the bottom. Emits nothing: callers that have already
        shown the newline themselves (PlainScreen's input echo) use it to
        keep the model - and so the word-wrap column - in step."""
        row, _col = self.lower_cursor
        if row + 1 >= self.height:
            self._scroll_lower()
        else:
            row += 1
        self.lower_cursor = (row, 0)

    def _scroll_lower(self) -> None:
        top = self.upper_height
        del self.rows[top]
        self.rows.append([Cell(" ", 0, self.fg, self.bg)] * self.width)

    def _put_upper(self, ch: str) -> None:
        row, col = self.upper_cursor
        if ch == "\n":
            self.upper_cursor = (row + 1, 0)
            return
        if row < self.upper_height and col < self.width:   # clip, never scroll
            self.rows[row][col] = Cell(ch, self.style, self.fg, self.bg)
        self.upper_cursor = (row, col + 1)

    # -------------------------------------------------------- window control
    def split_window(self, lines: int) -> None:
        """§15 split_window: upper window gets `lines` rows (0 = unsplit)."""
        self.flush()
        self.upper_height = max(0, min(lines, self.height))
        if self.lower_cursor[0] < self.upper_height:     # lower cursor stays below
            self.lower_cursor = (self.upper_height, 0)
        if self.upper_cursor[0] >= self.upper_height:
            self.upper_cursor = (0, 0)

    def set_window(self, window: int) -> None:
        self.flush()
        self.window = 1 if window == 1 else 0
        if self.window == 1:
            self.upper_cursor = (0, 0)       # §8.7.2: cursor to top left

    def erase_window(self, window: int) -> None:
        """§15 erase_window: -1 unsplit+clear all, -2 clear all, 0/1 one window."""
        self.flush()
        if window == -1:
            self.upper_height = 0
            self._clear_rows(0, self.height)
            self.lower_cursor = (0, 0)
        elif window == -2:
            self._clear_rows(0, self.height)
            self.lower_cursor = (self.upper_height, 0)
            self.upper_cursor = (0, 0)
        elif window == 0:
            self._clear_rows(self.upper_height, self.height)
            self.lower_cursor = (self.upper_height, 0)
        elif window == 1:
            self._clear_rows(0, self.upper_height)
            self.upper_cursor = (0, 0)
        self.lines_since_input = 0

    def _clear_rows(self, start: int, end: int) -> None:
        for r in range(start, end):
            self.rows[r] = [Cell(" ", 0, self.fg, self.bg)] * self.width

    def erase_line(self, value: int) -> None:
        """§15 erase_line 1: erase from the cursor to the end of the line."""
        if value != 1:
            return
        row, col = self.upper_cursor if self.window == 1 else self.lower_cursor
        for c in range(col, self.width):
            self.rows[row][c] = Cell(" ", 0, self.fg, self.bg)

    def set_cursor(self, line: int, column: int) -> None:
        """§15 set_cursor (1-based). In v5 only the upper window's cursor moves."""
        self.flush()
        if self.window == 1:
            self.upper_cursor = (max(0, line - 1), max(0, column - 1))

    def get_cursor(self) -> tuple[int, int]:
        row, col = self.upper_cursor if self.window == 1 else self.lower_cursor
        return row + 1, col + 1

    def set_text_style(self, style: int) -> None:
        self.flush()
        self.style = STYLE_ROMAN if style == 0 else (self.style | style)

    def set_colour(self, fg: int, bg: int) -> None:
        self.flush()
        if fg != COLOUR_CURRENT:
            self.fg = fg
        if bg != COLOUR_CURRENT:
            self.bg = bg

    def set_buffer_mode(self, on: bool) -> None:
        self.flush()
        self.buffering = on

    def set_font(self, font: int) -> int:
        """§15 set_font: 1 normal, 4 fixed-pitch. Returns the previous font,
        or 0 if the font is unavailable (we have no font 3 graphics)."""
        if font == 0:
            return self.font
        if font in (1, 4):
            previous, self.font = self.font, font
            return previous
        return 0

    def beep(self) -> None:
        pass

    # ----------------------------------------------------------------- input
    def read_line(self, max_length: int, initial: str = "") -> str:
        """Read a line for @read, echoing it into the lower window."""
        self.flush()
        self.render()
        text = self._input_line(max_length)[:max_length]
        for ch in text + "\n":
            self._put_lower(ch)
        self.lines_since_input = 0
        return text

    def read_key(self) -> int:
        self.flush()
        self.render()
        self.lines_since_input = 0
        return self._input_key()

    def _input_line(self, max_length: int) -> str:
        raise NotImplementedError

    def _input_key(self) -> int:
        raise NotImplementedError

    # -------------------------------------------------------------- display
    def render(self) -> None:
        """Draw the grid (curses). The model itself needs no drawing."""

    def more_prompt(self) -> None:
        """Pause when a screenful has scrolled past (curses shows [MORE])."""

    def close(self, reason: str = "") -> None:
        """End of session: flush any buffered text (curses also waits for a key)."""
        self.flush()

    # -------------------------------------------------------------- testing
    def text_rows(self) -> list[str]:
        return ["".join(cell.char for cell in row).rstrip() for row in self.rows]

    def transcript_text(self) -> str:
        return "".join(self.transcript)
