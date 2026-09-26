"""Tier 9: the terminal changes size under a running game.

The screen models keep what matters (v5/v7/v8: the status line and the
newest lines; v6: windows follow the screen's edges), and the machine tells
the game through the §11 header - asking a v6 game to redraw, as the §11
remarks suggest ("may be set by modern interpreters after, for example,
resizing the 'screen'")."""
from __future__ import annotations

from pathlib import Path

from zforge.common import header as H
from zforge.compiler.driver import compile_zil
from zforge.vm.headless import play
from zforge.vm.screen.virtual import VirtualScreen, VirtualV6Screen

ROOT = Path(__file__).resolve().parent.parent


def v5_screen_with_status_and_eight_lines():
    s = VirtualScreen(width=20, height=6)
    s.split_window(1)
    s.set_window(1)
    s.print("STATUS")
    s.set_window(0)
    for n in range(8):
        s.print(f"line {n}\n")
    s.flush()
    return s


def test_v5_shrinking_keeps_the_status_line_and_the_newest_lines():
    s = v5_screen_with_status_and_eight_lines()
    s.resize(12, 4)
    assert s.text_rows() == ["STATUS", "line 6", "line 7", ""]
    assert (s.width, s.height, s.upper_height) == (12, 4, 1)
    assert s.lower_cursor == (3, 0)              # still on its own (empty) line


def test_v5_growing_adds_blank_rows_below_and_keeps_the_cursor_with_the_text():
    s = v5_screen_with_status_and_eight_lines()
    s.resize(12, 4)
    s.resize(30, 8)
    assert s.text_rows() == ["STATUS", "line 6", "line 7", "", "", "", "", ""]
    assert s.lower_cursor == (3, 0)
    s.print("more\n")
    s.flush()
    assert s.text_rows()[3] == "more"


def test_v6_window_0_follows_the_edges_and_keeps_its_newest_lines():
    s = VirtualV6Screen(script=[], width=40, height=10)
    for n in range(12):
        s.print(f"line {n}\n")
    s.flush()
    s.resize(30, 5)
    w0 = s.windows[0]
    assert (w0.y_size, w0.x_size) == (5, 30)
    assert s.text_rows() == ["line 8", "line 9", "line 10", "line 11", ""]
    assert s.screen_cursor() == (4, 0)


def test_v6_a_window_inside_the_screen_keeps_its_size_until_the_edge_reaches_it():
    s = VirtualV6Screen(script=[], width=40, height=10)
    s.move_window(2, 3, 5)                       # (y, x), 1-based (§8.8.1)
    s.window_size(2, 3, 10)
    s.resize(60, 20)
    assert (s.windows[2].y_size, s.windows[2].x_size) == (3, 10)     # did not touch an edge
    s.resize(8, 4)
    assert (s.windows[2].y_size, s.windows[2].x_size) == (2, 4)      # rows 3-4, columns 5-8


def test_v6_screen_cursor_is_the_current_windows_cursor():
    s = VirtualV6Screen(script=[], width=40, height=10)
    s.move_window(2, 3, 5)
    s.window_size(2, 3, 10)
    s.set_window(2)
    s.set_cursor(2, 4, 2)                        # line 2, column 4 of window 2
    assert s.screen_cursor() == (3, 7)           # 0-based, on the screen


def test_the_machine_tells_the_game_the_new_size():
    story = compile_zil((ROOT / "examples" / "cloak.zil").read_text(), "cloak.zil").story
    result = play(story, ["quit", "y"])
    result.screen.resize(100, 30)
    mem = result.vm.mem
    assert mem.read_byte(H.H_SCREEN_HEIGHT_LINES) == 30
    assert mem.read_byte(H.H_SCREEN_WIDTH_CHARS) == 100
    assert mem.read_word(H.H_SCREEN_WIDTH_UNITS) == 100
    assert mem.read_word(H.H_SCREEN_HEIGHT_UNITS) == 30
    assert not mem.read_word(H.H_FLAGS2) & H.F2_REDRAW      # §11: the redraw bit is v6 only


def test_a_v6_game_is_also_asked_to_redraw():
    source = (ROOT / "examples" / "v6_windows.zil").read_text()
    result = play(compile_zil(source, "v6_windows.zil", 6).story, ["quit"])
    result.screen.resize(100, 30)
    mem = result.vm.mem
    assert mem.read_word(H.H_SCREEN_WIDTH_UNITS) == 100
    assert mem.read_word(H.H_FLAGS2) & H.F2_REDRAW


def test_the_same_size_changes_nothing():
    s = v5_screen_with_status_and_eight_lines()
    calls = []
    s.on_resize = lambda w, h: calls.append((w, h))
    before = s.text_rows()
    s.resize(20, 6)
    assert s.text_rows() == before and calls == []
