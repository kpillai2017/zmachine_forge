"""§8.8 The version-6 screen model: eight windows on one grid.

Version 6 was Infocom's graphical Z-machine. Its screen is an array of
PIXELS, and there are eight windows which lie on top of each other like
transparencies (§8.8.3). zforge is a character terminal, so it uses the
one honest simplification the Standard allows: ONE UNIT = ONE CHARACTER.
The font is 1 unit wide and 1 unit high (§11.1, header $26/$27), so every
coordinate in this file is a character cell, and "pixels" in the opcode
definitions means "cells". Pictures are not available (§8.8.5), which the
interpreter reports honestly: see `picture_data` in vm/ops/v6.py.

What the Standard says, and what that means here:

  §8.8.3    eight windows, numbered 0-7; -3 means "the current one"
  §8.8.3.1  four attributes: 0 wrapping, 1 scrolling, 2 transcript,
            3 buffering (set with window_style)
  §8.8.3.2  eighteen properties, read with get_wind_prop; only the
            newline interrupt, its countdown and the line count should be
            written with put_wind_prop
  §8.8.3.3  window 0 fills the screen and is selected; window 1 is full
            width and zero height; windows 2-7 are empty. All start at
            (1,1).
  §8.8.4.1  split_window tiles windows 0 and 1, as in v5
  §8.8.3.5  each window remembers its own cursor, and set_cursor may move
            another window's

Nothing here is v5 code with flags: GridScreen (the v5 model) still owns
the grid, the renderers and input. This mixin replaces the window methods
in front of it, so `class VirtualV6Screen(V6Model, VirtualScreen)` is a
v6 screen with scripted input.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from zforge.vm.screen.base import BLANK, Cell, COLOUR_DEFAULT, GridScreen, STYLE_ROMAN

WINDOW_COUNT = 8
CURRENT_WINDOW = -3            # §8.8.3: the window number meaning "the current one"

# §8.8.3.1 the four attributes, as bits of the attributes property (14)
ATTR_WRAPPING, ATTR_SCROLLING, ATTR_TRANSCRIPT, ATTR_BUFFERING = 1, 2, 4, 8

# §8.8.3.2 the property numbers, in the Standard's order
(P_Y, P_X, P_Y_SIZE, P_X_SIZE, P_Y_CURSOR, P_X_CURSOR, P_LEFT_MARGIN, P_RIGHT_MARGIN,
 P_INTERRUPT_ROUTINE, P_INTERRUPT_COUNTDOWN, P_TEXT_STYLE, P_COLOUR_DATA, P_FONT_NUMBER,
 P_FONT_SIZE, P_ATTRIBUTES, P_LINE_COUNT, P_TRUE_FOREGROUND, P_TRUE_BACKGROUND) = range(18)

NEVER_MORE = -999              # §8.8.3.2.6 a line count of -999 means "never pause"


@dataclass
class Window:
    """One of the eight windows (§8.8.3). Positions and sizes are in units
    (= characters here); cursors are 1-based and relative to the window."""
    number: int
    y: int = 1                 # position on the screen, 1-based (§8.8.1: (y,x))
    x: int = 1
    y_size: int = 0
    x_size: int = 0
    y_cursor: int = 1          # relative to this window's own origin (§8.8.3.5)
    x_cursor: int = 1
    attributes: int = ATTR_BUFFERING            # §8.8.3.3
    left_margin: int = 0
    right_margin: int = 0
    interrupt_routine: int = 0                  # packed address (§8.8.3.2.2)
    interrupt_countdown: int = 0
    line_count: int = 0
    style: int = STYLE_ROMAN
    fg: int = COLOUR_DEFAULT
    bg: int = COLOUR_DEFAULT
    font: int = 1
    word_buffer: list[str] = field(default_factory=list)   # §8.8.3.1.2 buffering
    lines_since_input: int = 0

    def has(self, attribute: int) -> bool:
        """Check if an attribute (wrapping, scrolling, transcript, buffering) is set."""
        return bool(self.attributes & attribute)

    # -- the window's rectangle on the screen, as 0-based grid coordinates
    @property
    def top(self) -> int:
        """The window's top-left row on the screen (0-based)."""
        return self.y - 1

    @property
    def left(self) -> int:
        """The window's top-left column on the screen (0-based)."""
        return self.x - 1

    @property
    def text_width(self) -> int:
        """How many characters fit on one line, inside the margins (§8.8.3.2.1)."""
        return max(0, self.x_size - self.left_margin - self.right_margin)


class V6Model:
    """The §8.8 window model, in front of GridScreen's grid and renderer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.windows = [Window(n) for n in range(WINDOW_COUNT)]
        # §8.8.3.3: all windows begin at (1,1); window 0 fills the screen and
        # is selected; window 1 is as wide as the screen with zero height;
        # windows 2-7 have zero width and height.
        w0, w1 = self.windows[0], self.windows[1]
        w0.y_size, w0.x_size = self.height, self.width
        w1.x_size = self.width
        # §8.8.3.3 lists window 0 as scrolling, transcript and buffering; the
        # note under §8.8.3.1.2.2 says window 0 also has wrapping on ("it
        # would normally be on for a window holding running text"), and that
        # is what interpreters do, so zforge follows the note (KNOWN_GAPS).
        w0.attributes = ATTR_WRAPPING | ATTR_SCROLLING | ATTR_TRANSCRIPT | ATTR_BUFFERING
        self.window = 0
        self.split_height = 0        # §8.8.4.2: remembers whether a split happened

    # ------------------------------------------------------------- plumbing
    @property
    def current(self) -> Window:
        return self.windows[self.window]

    def _window(self, number: int) -> Window:
        """§8.8.3: a window number, where -3 means the current window."""
        if number == CURRENT_WINDOW:
            return self.current
        if not 0 <= number < WINDOW_COUNT:
            raise IndexError(f"window {number} does not exist (§8.8.3: 0 to 7)")
        return self.windows[number]

    # -------------------------------------------------------------- resize
    def resize(self, width: int, height: int) -> None:
        """The terminal changed size. A window that reached the old right
        or bottom edge follows the new one; a scrolling window whose cursor
        line would fall off scrolls up just enough to keep it (its newest
        text survives); everything is clipped to the new screen. The machine
        then tells the game and asks it to redraw (§11)."""
        width, height = max(width, 1), max(height, 1)
        if (width, height) == (self.width, self.height):
            return
        old_width, old_height = self.width, self.height
        for w in self.windows:
            if w.y_size and w.top + w.y_size >= old_height:
                new_y_size = max(0, height - w.top)
                cut = w.y_cursor - new_y_size
                if cut > 0 and w.has(ATTR_SCROLLING):
                    self._scroll(w, cut)          # on the old grid, before cropping
                    w.y_cursor -= cut
                w.y_size = new_y_size
            if w.x_size and w.left + w.x_size >= old_width:
                w.x_size = max(0, width - w.left)
        self.rows = ([(row + [BLANK] * width)[:width] for row in self.rows[:height]]
                     + [[BLANK] * width for _ in range(height - min(height, old_height))])
        self.width, self.height = width, height
        for w in self.windows:
            w.y_size = max(0, min(w.y_size, height - w.top))
            w.x_size = max(0, min(w.x_size, width - w.left))
            w.y_cursor = max(1, min(w.y_cursor, max(w.y_size, 1)))
            w.x_cursor = max(1, min(w.x_cursor, max(w.x_size, 1)))
            w.lines_since_input = 0
        if self.on_resize:
            self.on_resize(width, height)

    def screen_cursor(self) -> tuple[int, int]:
        """The current window's cursor, on the screen (0-based)."""
        w = self.current
        return (min(w.top + w.y_cursor - 1, self.height - 1),
                min(w.left + w.x_cursor - 1, self.width - 1))

    # -------------------------------------------------------------- output
    def print(self, text: str) -> None:
        for ch in text:
            self._put_v6(ch)

    def _put_v6(self, ch: str) -> None:
        """Collect a character for the current window, buffering if needed."""
        w = self.current
        # With buffering on, hold back all characters except spaces and newlines.
        if w.has(ATTR_BUFFERING) and ch not in (" ", "\n"):
            w.word_buffer.append(ch)          # §8.8.3.1.2: hold the word back
            return
        self.flush()
        self._write_char(w, ch)

    def flush(self) -> None:
        """§8.8.3.1.2.2: with buffering on, a word that will not fit moves to
        the next line whole; with it off, text breaks mid-word (_write_char)."""
        w = self.current
        if not w.word_buffer:
            return
        word, w.word_buffer = "".join(w.word_buffer), []
        # Check if the buffered word would overfill the current line.
        if (w.has(ATTR_WRAPPING) and w.x_cursor > w.left_margin + 1
                and w.x_cursor - 1 - w.left_margin + len(word) > w.text_width):
            self._write_char(w, "\n")   # the word moves down whole (§8.8.3.1.2.2)
        for ch in word:
            self._write_char(w, ch)

    def _write_char(self, w: Window, ch: str) -> None:
        """Write one character to a window, handling newlines, wrapping and
        clipping. Every character is recorded in the transcript (if that
        attribute is set) so z5 and z6 stories read identically."""
        # The transcript (attribute 2, output stream 2) sees each character
        # as the game printed it, exactly as the v5 model records it in
        # base.py - so the same story reads the same on z5 and z6.
        if w.has(ATTR_TRANSCRIPT):
            self.transcript.append(ch)
        # A newline ends the line and moves to the next (scrolling if needed).
        if ch == "\n":
            self._newline(w, wrapped=False)
            return
        # If the cursor is at the right margin, check the wrapping attribute.
        if w.x_cursor - 1 >= w.left_margin + w.text_width:
            # §8.8.3.1.1: with wrapping, carry on below; without it, the
            # cursor sits at the right margin and further text is ignored.
            if not w.has(ATTR_WRAPPING):
                return
            self._newline(w)
        # Skip a space that starts a line after a word wrap (not after explicit newline).
        if ch == " " and w.x_cursor == w.left_margin + 1 and self._wrapped:
            self._wrapped = False
            return                    # a wrapped line does not start with a space
        self._wrapped = False
        # Write the character to the grid if it is within the window's bounds.
        row, col = w.top + w.y_cursor - 1, w.left + w.x_cursor - 1
        if 0 <= row < self.height and 0 <= col < self.width and w.y_cursor <= w.y_size:
            self.rows[row][col] = Cell(ch, w.style, w.fg, w.bg)
            self._emit(ch)
        w.x_cursor += 1

    _wrapped = False           # the last newline was a wrap, not a printed "\n"

    def _newline(self, w: Window, wrapped: bool = True) -> None:
        """Move to the start of the next line inside the window. The caller
        has already recorded the character, if there was one."""
        self._wrapped = wrapped
        self._emit("\n")
        # Move the cursor to the start of the next line (at the left margin).
        w.x_cursor = w.left_margin + 1
        # If the cursor is not yet at the bottom, advance it; otherwise scroll if needed.
        if w.y_cursor < w.y_size:
            w.y_cursor += 1
        elif w.has(ATTR_SCROLLING):
            # A scrolling window shifts its text up to make room (§8.8.3.6).
            self._scroll(w, 1)
        # Track lines for the [MORE] prompt and the newline interrupt (§8.8.3.2.6).
        self._count_line(w)

    def _count_line(self, w: Window) -> None:
        """§8.8.3.2.2 the newline interrupt, and §8.8.3.2.6 the [MORE] prompt."""
        if w.interrupt_countdown:
            w.line_count = max(NEVER_MORE, w.line_count - 1)
            if w.line_count == 0 and w.interrupt_routine:
                self.pending_interrupt = w.interrupt_routine   # the VM runs it
        # Never pause if the line count is NEVER_MORE (-999).
        if w.line_count == NEVER_MORE:
            return
        # Track lines printed and pause when the window fills.
        w.lines_since_input += 1
        if w.y_size > 1 and w.lines_since_input >= w.y_size - 1:
            self.more_prompt()
            w.lines_since_input = 0

    pending_interrupt = 0        # §8.8.3.2.2: set here, called by the VM

    def _scroll(self, w: Window, lines: int) -> None:
        """§8.8.3.6 scroll_window: move a window's contents by `lines` (a
        negative value scrolls backwards), filling with background colour."""
        blank = Cell(" ", 0, w.fg, w.bg)
        for _ in range(abs(lines)):
            # Collect the window's rows and columns on the grid.
            rows = [self.rows[r] for r in range(w.top, min(w.top + w.y_size, self.height))]
            if not rows:
                return
            columns = range(w.left, min(w.left + w.x_size, self.width))
            # Decide the order to avoid overwriting before copying: scroll down
            # copies from bottom to top, scroll up copies from top to bottom.
            order = range(len(rows) - 1) if lines > 0 else range(len(rows) - 1, 0, -1)
            step = 1 if lines > 0 else -1
            # Shift each row and fill the edge with blanks.
            for i in order:
                for c in columns:
                    rows[i][c] = rows[i + step][c]
            edge = rows[-1] if lines > 0 else rows[0]
            for c in columns:
                edge[c] = blank

    # ------------------------------------------------------- window control
    def set_window(self, window: int) -> None:
        """§15 set_window. §8.7.2 (v5) puts the cursor at the top left of the
        upper window; §8.8.3.5 gives every v6 window a cursor it remembers."""
        self.flush()
        self.window = self._window(window).number

    def split_window(self, lines: int) -> None:
        """§8.8.4.1: tile windows 0 and 1, window 1 on top with `lines` units."""
        self.flush()
        lines = max(0, min(lines, self.height))
        w0, w1 = self.windows[0], self.windows[1]
        # Window 1 (status line) is at (1,1) with the given height; window 0 below it.
        w1.y, w1.x, w1.y_size, w1.x_size = 1, 1, lines, self.width
        w0.y, w0.x = lines + 1, 1
        w0.y_size, w0.x_size = self.height - lines, self.width
        self.split_height = lines
        # If a window's cursor is now outside its bounds, reset it.
        for w in (w0, w1):
            if w.y_cursor > w.y_size:
                w.y_cursor, w.x_cursor = 1, w.left_margin + 1

    def window_size(self, window: int, y: int, x: int) -> None:
        """§15 window_size: resize, and (§8.8.3.4) rescue a stranded cursor."""
        w = self._window(window)
        w.y_size, w.x_size = max(0, y), max(0, x)
        # If the cursor is now outside the window, move it inside (top-left).
        if w.y_cursor > w.y_size or w.x_cursor > w.x_size:
            w.y_cursor, w.x_cursor = 1, w.left_margin + 1

    def move_window(self, window: int, y: int, x: int) -> None:
        """§15 move_window: "nothing actually happens" - what was printed
        stays where it was; only later printing goes to the new place."""
        w = self._window(window)
        w.y, w.x = max(1, y), max(1, x)

    def window_style(self, window: int, flags: int, operation: int = 0) -> None:
        """§15 window_style: 0 set, 1 set these bits, 2 clear them, 3 flip them."""
        w = self._window(window)
        w.attributes = {0: flags, 1: w.attributes | flags,
                        2: w.attributes & ~flags, 3: w.attributes ^ flags}[operation & 3]

    def set_margins(self, left: int, right: int, window: int = CURRENT_WINDOW) -> None:
        """§15 set_margins, §8.8.3.2.1. If the cursor is left outside the
        margins it moves back to the left margin of the current line."""
        w = self._window(window)
        w.left_margin, w.right_margin = max(0, left), max(0, right)
        # If the cursor is now outside the margins, reset it to the left margin.
        if w.x_cursor <= w.left_margin or w.x_cursor - 1 > w.left_margin + w.text_width:
            w.x_cursor = w.left_margin + 1

    def scroll_window(self, window: int, pixels: int) -> None:
        """§15 scroll_window: any window, whatever its scrolling attribute."""
        self._scroll(self._window(window), pixels)

    def erase_window(self, window: int) -> None:
        """§15 erase_window. §8.8.4.2: erasing the whole screen also unsplits
        windows 0 and 1, if they were split."""
        self.flush()
        # Erase -1 or -2: clear all windows and reset all cursors.
        if window in (-1, -2):
            for w in self.windows:
                w.lines_since_input = 0
            self._clear_rows(0, self.height)
            # Erase -1 also unsplits: return window 0 and 1 to their defaults.
            if window == -1 and self.split_height:
                self.split_window(0)
            for w in self.windows:
                w.y_cursor, w.x_cursor = 1, w.left_margin + 1
            return
        # Erase one window: clear its rectangle on the grid and reset its cursor.
        w = self._window(window)
        blank = Cell(" ", 0, w.fg, w.bg)
        for r in range(w.top, min(w.top + w.y_size, self.height)):
            for c in range(w.left, min(w.left + w.x_size, self.width)):
                self.rows[r][c] = blank
        w.y_cursor, w.x_cursor = 1, w.left_margin + 1
        w.lines_since_input = 0

    def erase_line(self, value: int) -> None:
        """§8.8.5.2: erase from the cursor to the right margin (value 1), or
        that many units to the right, in background colour."""
        if value < 1:
            return
        w = self.current
        row = w.top + w.y_cursor - 1
        if not 0 <= row < self.height:
            return
        # Erase from the cursor to the right margin (value 1) or for value units.
        first = w.left + w.x_cursor - 1
        last = (w.left + w.x_size - w.right_margin) if value == 1 else (first + value)
        for c in range(first, min(last, self.width)):
            self.rows[row][c] = Cell(" ", 0, w.fg, w.bg)

    def set_cursor(self, line: int, column: int, window: int = CURRENT_WINDOW) -> None:
        """§15 set_cursor: (line, column) in units, 1-based, in any window.
        set_cursor -1 hides the cursor and -2 shows it again."""
        if line == -1 or line == -2:
            self.cursor_visible = line == -2
            return
        self.flush()
        w = self._window(window)
        w.y_cursor, w.x_cursor = max(1, line), max(1, column)

    cursor_visible = True

    def get_cursor(self) -> tuple[int, int]:
        """§8.8.3.2.7: buffered text is flushed first, so the answer is true."""
        self.flush()
        w = self.current
        return w.y_cursor, w.x_cursor

    # ------------------------------------------------------ style and colour
    def set_text_style(self, style: int) -> None:
        """§15 set_text_style: set or reset text attributes (roman, bold, etc.)."""
        self.flush()
        w = self.current
        w.style = STYLE_ROMAN if style == 0 else (w.style | style)

    def set_colour(self, fg: int, bg: int, window: int = CURRENT_WINDOW) -> None:
        """§15 set_colour: v6 takes the window as a third operand. Each window
        remembers its own pair, so it survives switching away and back."""
        self.flush()
        w = self._window(window)
        if fg:
            w.fg = fg
        if bg:
            w.bg = bg

    def set_font(self, font: int, window: int = CURRENT_WINDOW) -> int:
        """§15 set_font: font 0 asks which font is in use; 1 (normal) and 4
        (fixed-pitch) are the ones a character terminal has (§8.1.2)."""
        w = self._window(window)
        previous = w.font
        if font == 0 or font in (1, 4):
            w.font = w.font if font == 0 else font
            return previous
        return 0                              # §15: 0 means "not available"

    def set_buffer_mode(self, on: bool) -> None:
        """§15 buffer_mode is "undefined" in v6 (the window attribute does the
        job). zforge does what Frotz does: set the current window's
        buffering attribute, which is what the opcode plainly means."""
        self.flush()
        w = self.current
        w.attributes = (w.attributes | ATTR_BUFFERING) if on else (w.attributes & ~ATTR_BUFFERING)

    # ------------------------------------------------------------ properties
    def get_window_property(self, window: int, number: int) -> int:
        """§8.8.3.2 get_wind_prop: the eighteen properties, in order."""
        w = self._window(window)
        # Return the property value: position, size, cursor, margins, style, colours, etc.
        values = {
            P_Y: w.y, P_X: w.x, P_Y_SIZE: w.y_size, P_X_SIZE: w.x_size,
            P_Y_CURSOR: w.y_cursor, P_X_CURSOR: w.x_cursor,
            P_LEFT_MARGIN: w.left_margin, P_RIGHT_MARGIN: w.right_margin,
            P_INTERRUPT_ROUTINE: w.interrupt_routine,
            P_INTERRUPT_COUNTDOWN: w.interrupt_countdown,
            P_TEXT_STYLE: w.style,
            # §8.8.3.2.4 foreground in the lower byte, background in the upper
            P_COLOUR_DATA: (w.bg << 8) | w.fg,
            P_FONT_NUMBER: w.font,
            # §8.8.3.2.5 height in the upper byte, width in the lower: 1 unit each
            P_FONT_SIZE: (1 << 8) | 1,
            P_ATTRIBUTES: w.attributes, P_LINE_COUNT: w.line_count,
            P_TRUE_FOREGROUND: w.fg, P_TRUE_BACKGROUND: w.bg,
        }
        if number not in values:
            raise IndexError(f"window property {number} does not exist (§8.8.3.2: 0 to 17)")
        return values[number]

    def put_window_property(self, window: int, number: int, value: int) -> None:
        """§15 put_wind_prop. The Standard says a game should only write the
        newline interrupt, its countdown and the line count; the others are
        the interpreter's, or have opcodes of their own. zforge allows the
        writeable ones (0-15) and ignores the rest, as §8.8.3.2 requires for
        the two true-colour properties."""
        w = self._window(window)
        # Map property numbers to window attributes that the game may write.
        writeable = {
            P_Y: "y", P_X: "x", P_Y_SIZE: "y_size", P_X_SIZE: "x_size",
            P_Y_CURSOR: "y_cursor", P_X_CURSOR: "x_cursor",
            P_LEFT_MARGIN: "left_margin", P_RIGHT_MARGIN: "right_margin",
            P_INTERRUPT_ROUTINE: "interrupt_routine",
            P_INTERRUPT_COUNTDOWN: "interrupt_countdown",
            P_TEXT_STYLE: "style", P_FONT_NUMBER: "font",
            P_ATTRIBUTES: "attributes", P_LINE_COUNT: "line_count",
        }
        # Colour data is packed: foreground in the lower byte, background in the upper.
        if number == P_COLOUR_DATA:
            w.fg, w.bg = value & 0xFF, (value >> 8) & 0xFF
        elif number in writeable:
            setattr(w, writeable[number], value)

    # ---------------------------------------------------------------- input
    def read_line(self, max_length: int, initial: str = "") -> str:
        """@read: the typed line is echoed into the CURRENT window, at its
        own cursor (§8.8.3.5) - not into the v5 lower window."""
        self.flush()
        self.render()
        text = self._input_line(max_length)[:max_length]
        w = self.current
        for ch in text + "\n":
            self._write_char(w, ch)
        w.lines_since_input = 0
        return text

    def read_key(self) -> int:
        """§15 read_char: read one key press and return its ZSCII code."""
        self.flush()
        self.render()
        self.current.lines_since_input = 0
        return self._input_key()

    # ------------------------------------------------------------- rendering
    def text_rows(self) -> list[str]:
        """Return the visible text of each row (for tests and --ui plain)."""
        return ["".join(cell.char for cell in row).rstrip() for row in self.rows]


class V6GridScreen(V6Model, GridScreen):
    """The v6 model on a bare grid: the base for the renderers below."""


def blank_row(width: int) -> list[Cell]:
    return [BLANK] * width
