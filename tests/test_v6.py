"""Version 6: the eight-window screen model (§8.8), its eighteen extra
opcodes, and the two things that make a v6 story file different (§5.4
starts by calling a routine, §11.1 swaps the two font-size bytes).

The rule these tests keep: a story that does not use any v6 feature must
read exactly the same on z6 as it does on z5. Everything else about v6 -
windows, margins, user stacks - is checked against the Standard's own
worked examples where it gives them.
"""
from pathlib import Path

import pytest

from zforge.common.header import Header
from zforge.common.opcodes import table_for
from zforge.common.versions import profile_for
from zforge.compiler.driver import compile_zil
from zforge.compiler.i7.driver import compile_i7
from zforge.vm.headless import play
from zforge.vm.ops import handlers_for
from zforge.vm.screen.v6 import ATTR_BUFFERING, ATTR_WRAPPING
from zforge.vm.screen.virtual import VirtualV6Screen

ROOT = Path(__file__).resolve().parent.parent


def screen(width=40, height=10, **kwargs):
    s = VirtualV6Screen(script=[], width=width, height=height, **kwargs)
    return s


def run_zil(body: str, commands=(), width=80):
    """Compile a v6 fragment and play it. USTACK is a user stack with room
    for two values (§6.6: its first word is the number of free slots);
    INFO is a four-word array for read_mouse and picture_data."""
    source = ("<VERSION 6>\n"
              "<GLOBAL USTACK <TABLE 2 0 0>>\n"
              "<GLOBAL INFO <TABLE 0 0 0 0>>\n"
              f"<ROUTINE GO ()\n{body}\n\t<QUIT>>\n")
    return play(compile_zil(source, "t.zil", 6).story, list(commands), width=width)


# --------------------------------------------------------------- the file
def test_a_v6_story_starts_by_calling_its_main_routine():
    """§5.4: the word at $06 is the PACKED address of "main"."""
    story = compile_zil((ROOT / "examples/hello.zil").read_text(), "hello.zil", 6).story
    h = Header.parse(story)
    assert h.profile.starts_with_main_routine
    assert h.main_routine == h.profile.unpack_routine(h.initial_pc, h.routines_offset)
    assert story[h.main_routine] == 0            # §5.2: the stub has no locals
    assert h.main_routine >= h.high_memory


def test_v6_swaps_the_two_font_size_bytes():
    """§11.1: v5 has width at $26 and height at $27; v6 has them the other
    way round. Both are 1 here (one unit is one character), so the test
    checks the addresses, not the values."""
    assert Header.parse(_story(5)).font_size_bytes() == (0x26, 0x27)
    assert Header.parse(_story(6)).font_size_bytes() == (0x27, 0x26)


def _story(version: int) -> bytes:
    return compile_zil((ROOT / "examples/hello.zil").read_text(), "hello.zil", version).story


def test_every_v6_opcode_has_a_handler():
    """§14: v6 adds eighteen opcodes and removes none."""
    v5, v6 = table_for(5), table_for(6)
    assert len(v6) - len(v5) == 18
    handlers = handlers_for(6)
    missing = sorted(op.name for op in v6.values()
                     if op.name not in handlers and not op.name.startswith("ext_unknown"))
    assert missing == []


def test_a_v6_source_builds_only_for_z6():
    from zforge.compiler.driver import compatible_targets
    assert compatible_targets(6) == [6]


# ------------------------------------------------------- the window model
def test_the_standard_s_own_wrapping_example():
    """§8.8.3.1.2.2 prints "Here is an abacus" in a narrow window and gives
    the result for all four combinations of wrapping and buffering,
    including where the cursor ends up (its caret)."""
    expected = {
        (True, True): (["Here is an", "abacus"], (2, 7)),
        (False, True): (["Here is an aba"], (1, 15)),
        (True, False): (["Here is an aba", "cus"], (2, 4)),
        (False, False): (["Here is an aba"], (1, 15)),
    }
    for (wrapping, buffering), (lines, caret) in expected.items():
        s = screen(width=14, height=5)
        w = s.windows[0]
        w.attributes = (ATTR_WRAPPING if wrapping else 0) | (ATTR_BUFFERING if buffering else 0)
        s.print("Here is an abacus")
        s.flush()
        assert [r for r in s.text_rows() if r] == lines, (wrapping, buffering)
        assert s.get_cursor() == caret, (wrapping, buffering)


def test_the_default_windows():
    """§8.8.3.3: all eight begin at (1,1); window 0 fills the screen and is
    selected; window 1 is full width and zero height; 2-7 are empty."""
    s = screen(width=80, height=24)
    assert len(s.windows) == 8 and s.window == 0
    assert all((w.y, w.x) == (1, 1) for w in s.windows)
    assert (s.windows[0].y_size, s.windows[0].x_size) == (24, 80)
    assert (s.windows[1].y_size, s.windows[1].x_size) == (0, 80)
    assert all((w.y_size, w.x_size) == (0, 0) for w in s.windows[2:])
    assert s.windows[0].attributes == 15                 # all four on
    assert all(w.attributes == ATTR_BUFFERING for w in s.windows[1:])


def test_split_window_tiles_windows_0_and_1():
    """§8.8.4.1: window 1 goes on top with the given height, window 0 below."""
    s = screen(width=80, height=24)
    s.split_window(3)
    assert (s.windows[1].y, s.windows[1].y_size) == (1, 3)
    assert (s.windows[0].y, s.windows[0].y_size) == (4, 21)


def test_erase_window_minus_one_unsplits():
    """§8.8.4.2: erasing the whole screen unsplits, if a split had happened."""
    s = screen(width=80, height=24)
    s.split_window(3)
    s.erase_window(-1)
    assert s.windows[1].y_size == 0 and s.windows[0].y_size == 24


def test_each_window_keeps_its_own_cursor_and_colours():
    """§8.8.3.5 and the §8.8 remark: "each window must remember accurately
    the colour pair selected, so it is preserved across window switches"."""
    s = screen()
    s.split_window(2)
    s.set_cursor(2, 5, 1)
    s.set_colour(4, 2, 1)                 # green on black, window 1 only
    s.set_window(1)
    assert s.get_cursor() == (2, 5)
    s.set_window(0)
    assert s.get_cursor() == (1, 1)
    assert (s.windows[1].fg, s.windows[1].bg) == (4, 2)
    assert (s.windows[0].fg, s.windows[0].bg) == (1, 1)


def test_margins_indent_text_and_wrap_it_early():
    """§8.8.3.2.1: text is clipped to stay inside the margins, and after a
    new-line the cursor moves to the left margin of the next line."""
    s = screen(width=20, height=6)
    s.set_margins(4, 4, 0)
    s.print("one two three four five six")
    s.flush()
    rows = [r for r in s.text_rows() if r]
    assert all(r.startswith("    ") for r in rows)
    assert all(len(r) <= 16 for r in rows)


def test_set_margins_rescues_a_stranded_cursor():
    """§8.8.3.2.1: if the cursor is left outside the margins it moves back
    to the left margin of the current line."""
    s = screen(width=20, height=6)
    s.set_cursor(1, 2)
    s.set_margins(6, 0, 0)
    assert s.get_cursor() == (1, 7)


def test_window_properties_read_back():
    """§8.8.3.2: the eighteen properties, in the Standard's order."""
    s = screen(width=80, height=24)
    s.move_window(2, 3, 5)
    s.window_size(2, 6, 20)
    s.set_colour(4, 2, 2)
    assert s.get_window_property(2, 0) == 3         # y
    assert s.get_window_property(2, 1) == 5         # x
    assert s.get_window_property(2, 2) == 6         # y size
    assert s.get_window_property(2, 3) == 20        # x size
    assert s.get_window_property(2, 11) == (2 << 8) | 4    # §8.8.3.2.4 colour data
    assert s.get_window_property(2, 13) == (1 << 8) | 1    # §8.8.3.2.5 font size 1x1
    assert s.get_window_property(2, 14) == ATTR_BUFFERING  # attributes


def test_window_number_minus_three_means_the_current_window():
    """§8.8.3: "The code -3 is used as a window number"."""
    s = screen()
    s.set_window(1)
    s.set_margins(2, 2, -3)
    assert s.windows[1].left_margin == 2 and s.windows[0].left_margin == 0


def test_window_style_sets_clears_and_flips():
    """§15 window_style: operation 0 set, 1 or, 2 clear, 3 flip."""
    s = screen()
    s.window_style(0, 0b1111, 0)
    assert s.windows[0].attributes == 0b1111
    s.window_style(0, 0b0001, 2)
    assert s.windows[0].attributes == 0b1110
    s.window_style(0, 0b0011, 3)
    assert s.windows[0].attributes == 0b1101
    s.window_style(0, 0b0010, 1)
    assert s.windows[0].attributes == 0b1111


def test_scroll_window_moves_a_window_s_contents():
    """§8.8.3.6: any window, either way, whatever its scrolling attribute."""
    s = screen(width=10, height=4)
    s.print("one\ntwo\n")
    s.flush()
    s.scroll_window(0, 1)
    assert [r for r in s.text_rows() if r] == ["two"]


def test_a_window_without_scrolling_stays_on_its_last_line():
    """§8.8.3.1: scrolling is an attribute, and window 2 has it off. What
    happens when text reaches the bottom of such a window is "undefined
    behaviour" (the §8.8 remark), so zforge makes a choice and keeps to
    it: the cursor stays on the last line and later text overwrites it.
    Nothing is ever painted outside the window."""
    s = screen(width=10, height=6)
    s.window_size(2, 2, 10)
    s.set_window(2)
    s.print("one\ntwo\nthree\n")
    s.flush()
    assert [r for r in s.text_rows() if r] == ["one", "three"]


# ------------------------------------------------------------- the opcodes
def test_get_wind_prop_and_margins_from_zil():
    out = run_zil('''\t<SPLIT 3>
\t<PRINTI "y size of window 1 = ">
\t<PRINTN <WINGET 1 2>>
\t<CRLF>
\t<MARGIN 4 4 0>
\t<PRINTI "indented">''')
    assert "y size of window 1 = 3" in out.transcript
    assert any(r.startswith("    indented") for r in out.screen.text_rows())


def test_user_stacks():
    """§6.6: the first word of a user stack holds the number of free slots.
    §15 push_stack branches if the value fitted; an overflow is not an error."""
    out = run_zil('''\t<PRINTN <GET ,USTACK 0>>
\t<COND (<XPUSH 111 ,USTACK> <PRINTI " pushed">) (T <PRINTI " full">)>
\t<COND (<XPUSH 222 ,USTACK> <PRINTI " pushed">) (T <PRINTI " full">)>
\t<COND (<XPUSH 333 ,USTACK> <PRINTI " pushed">) (T <PRINTI " full">)>
\t<PRINTI " free: ">
\t<PRINTN <GET ,USTACK 0>>''')
    assert "2 pushed pushed full free: 0" in out.transcript


def test_pull_stores_its_result_in_v6():
    """§15 pull: in v6 it stores, so a v5 source that uses `pull` without a
    destination is refused by the assembler with that in the message."""
    from zforge.asm.assembler import assemble
    from zforge.common.errors import ZForgeError
    source = ".routine main 0\n\tpush 1\n\tpull sp\n\tquit\n.end\n"
    assemble(source, "t.zas", 5)                      # fine in v5
    with pytest.raises(ZForgeError, match="pull stores a result"):
        assemble(source, "t.zas", 6)


def test_there_are_no_pictures_and_the_game_is_told_so():
    """§8.8.5 and §15 picture_data: with no picture file, asking about
    picture 0 writes zero pictures available and does not branch."""
    out = run_zil('''\t<COND (<PICINF 0 ,INFO> <PRINTI "pictures">) (T <PRINTI "no pictures">)>
\t<PRINTI ", count = ">
\t<PRINTN <GET ,INFO 0>>''')
    assert "no pictures, count = 0" in out.transcript


def test_no_mouse_reports_the_pointer_at_rest():
    out = run_zil('''\t<MOUSE-INFO ,INFO>
\t<PRINTN <GET ,INFO 2>>''')          # button bits: none held
    assert out.transcript.strip().endswith("0")


# ------------------------------------------- a v6 story reads like a v5 one
@pytest.mark.parametrize("example", ["hello.zil", "cloak.zil", "parser_demo.zil"])
def test_the_same_zil_reads_the_same_on_z5_and_z6(example):
    source = (ROOT / "examples" / example).read_text()
    commands = ["w", "hang cloak on hook", "e", "s", "read message", "quit", "y"]
    on = {v: play(compile_zil(source, example, v).story, commands).transcript for v in (5, 6)}
    assert on[5] == on[6]


def test_an_i7_story_reads_the_same_on_z5_and_z6():
    source = (ROOT / "examples/advent_opening.ni").read_text()
    commands = ["no", "in", "take lamp", "take food", "i", "out", "s", "s", "quit", "y"]
    on = {v: play(compile_i7(source, "advent.ni", v).story, commands).transcript for v in (5, 6)}
    assert on[5] == on[6]


def test_the_v6_demo_draws_its_panel():
    """examples/v6_windows.zil: a bordered panel in window 2, text flowing
    beside it in window 0, a status bar in window 1."""
    story = compile_zil((ROOT / "examples/v6_windows.zil").read_text(), "v6_windows.zil").story
    assert Header.parse(story).version == 6
    rows = play(story, ["move", "quit"]).screen.text_rows()
    assert rows[0].startswith(" zforge v6 demo")                 # window 1
    assert any(r.endswith("+") and "+---" in r for r in rows)    # the panel's border
    assert any("| window 2" in r for r in rows)                  # its own text
    assert any(r.startswith("The version-6 screen model") for r in rows)   # window 0


def test_v6_is_not_offered_as_a_bigger_target():
    """A v5 story that outgrows 256K should be told about z7 and z8, not v6:
    v6 has other opcodes, so it is not a drop-in (§1.1.4, §8.8)."""
    assert profile_for(5).larger_versions() == [7, 8]
