"""Tier 9: the curses renderer, driven through real games WITHOUT a
terminal. FakeWindow stands in for curses' stdscr: it records what is drawn
and hands out scripted keys, so these tests exercise the real CursesScreen
and CursesV6Screen code - drawing, the line editor, resizing, the cursor.
(tests/test_curses_tty.py runs the real thing in a pseudo-terminal.)"""
from __future__ import annotations

from pathlib import Path

import pytest

curses = pytest.importorskip("curses")

from zforge.common import header as H                                   # noqa: E402
from zforge.compiler.driver import compile_zil                          # noqa: E402
from zforge.vm.machine import ZMachine                                  # noqa: E402
from zforge.vm.screen.curses_screen import CursesScreen, CursesV6Screen  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


class FakeWindow:
    """Just enough of a curses window. A key ("resize", rows, columns)
    changes its size and delivers KEY_RESIZE, as a real terminal would.
    Every time a key is asked for, it keeps a snapshot of the screen."""

    def __init__(self, keys, height=24, width=80):
        self.keys = list(keys)
        self.height, self.width = height, width
        self.cells: dict[tuple[int, int], str] = {}
        self.cursor = (0, 0)
        self.snapshots: list[tuple[list[str], tuple[int, int]]] = []

    def getmaxyx(self):
        return self.height, self.width

    def keypad(self, flag):
        pass

    def addstr(self, y, x, text, attr=0):
        if not (0 <= y < self.height and 0 <= x < self.width):
            raise curses.error("outside the window")
        for i, ch in enumerate(text[:self.width - x]):
            self.cells[(y, x + i)] = ch

    def move(self, y, x):
        self.cursor = (y, x)

    def refresh(self):
        pass

    def clear(self):
        self.cells = {}

    def rows(self) -> list[str]:
        return ["".join(self.cells.get((r, c), " ") for c in range(self.width)).rstrip()
                for r in range(self.height)]

    def get_wch(self):
        self.snapshots.append((self.rows(), self.cursor))
        if not self.keys:
            raise KeyboardInterrupt           # the tests' way to end a game
        key = self.keys.pop(0)
        if isinstance(key, tuple):
            _, self.height, self.width = key
            return curses.KEY_RESIZE
        return key


@pytest.fixture
def cursor_calls(monkeypatch):
    """curses functions that need a real terminal become no-ops; curs_set
    calls are recorded."""
    calls: list[int] = []
    for name in ("noecho", "cbreak"):
        monkeypatch.setattr(curses, name, lambda: None)
    monkeypatch.setattr(curses, "has_colors", lambda: False)
    monkeypatch.setattr(curses, "curs_set", calls.append)
    return calls


def run(screen_class, story: bytes, window: FakeWindow) -> ZMachine:
    screen = screen_class(window)
    vm = ZMachine(story, screen, seed=1)
    reason = vm.run(max_steps=5_000_000)
    assert reason == "interrupted"
    return vm


def v6_demo() -> bytes:
    source = (ROOT / "examples" / "v6_windows.zil").read_text()
    return compile_zil(source, "v6_windows.zil", 6).story


def cloak() -> bytes:
    return compile_zil((ROOT / "examples" / "cloak.zil").read_text(), "cloak.zil").story


def test_v6_typing_appears_at_the_current_windows_cursor_and_wipes_nothing(cursor_calls):
    window = FakeWindow(list("wrap"))
    run(CursesV6Screen, v6_demo(), window)
    before, _ = window.snapshots[0]               # the screen as the game drew it
    during, (row, col) = window.snapshots[-1]     # after typing "wrap"
    assert during[row].endswith("> wrap") and col == len(during[row])
    for r, line in enumerate(before):             # every other row is untouched
        if r != row:
            assert during[r] == line, (r, line, during[r])


def test_a_resize_reaches_the_game_and_its_status_line_grows(cursor_calls):
    window = FakeWindow([("resize", 30, 100), *"look", "\n"])
    vm = run(CursesScreen, cloak(), window)
    assert vm.mem.read_byte(H.H_SCREEN_WIDTH_CHARS) == 100
    assert vm.mem.read_byte(H.H_SCREEN_HEIGHT_LINES) == 30
    status = window.rows()[0]
    assert len(status) > 80                        # the score now sits at column 80 (100 - 20)
    assert any("Foyer of the Opera House" in line for line in window.rows()[1:])


def test_a_resize_while_typing_keeps_what_was_typed(cursor_calls):
    window = FakeWindow([*"lo", ("resize", 20, 60), *"ok"])
    run(CursesScreen, cloak(), window)
    rows, (row, col) = window.snapshots[-1]
    assert rows[row].endswith(">look") or rows[row].endswith("> look")
    assert (window.height, window.width) == (20, 60)


def test_the_cursor_is_shown_and_hidden_as_the_game_asks(cursor_calls):
    screen = CursesV6Screen(FakeWindow([]))
    screen.render()
    screen.set_cursor(-1, 0)                        # §15 set_cursor: -1 hides the cursor
    screen.render()
    screen.set_cursor(-2, 0)                        # -2 shows it again
    screen.render()
    assert cursor_calls == [1, 0, 1]
