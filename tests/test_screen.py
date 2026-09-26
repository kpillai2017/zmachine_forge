"""§8 screen model on the VirtualScreen grid."""
from tests.conftest import zil


def row(r, n):
    return "".join(c.char for c in r.screen.rows[n])


def test_upper_window_cursor_and_reverse_video():
    r = zil("<SPLIT 1> <SCREEN 1> <CURSET 1 5> <HLIGHT 1> <TELL \"STATUS\"> <HLIGHT 0>"
            "<SCREEN 0> <TELL \"body\" CR>")
    assert row(r, 0)[4:10] == "STATUS" and r.screen.rows[0][4].style & 1
    assert "body" in r.transcript and "STATUS" not in r.transcript


def test_word_wrap_never_splits_words():
    """The TRANSCRIPT is logical text; wrapping happens on the screen grid."""
    words = [f"word{i}" for i in range(40)]
    r = zil(f'<TELL "{" ".join(words)}" CR>')
    rows = [row(r, n).rstrip() for n in range(r.screen.height)]
    shown = [w for line in rows if line for w in line.split()]
    assert shown == words                          # no word was cut in two
    assert all(not line.startswith(" ") for line in rows if line)


def test_erase_window_minus_one_unsplits():
    r = zil("<SPLIT 3> <CLEAR -1> <SCREEN 1> <TELL \"x\"> <SCREEN 0>")
    assert r.screen.upper_height == 0


def test_plain_screen_wrap_column_restarts_after_input():
    """Games like Advent re-prompt on the SAME line ("Please respond yes or
    no. > "). After each input line the model's cursor must be back at
    column 0, or the word-wrap drifts earlier every turn."""
    import io

    from zforge.vm.screen.plain import PlainScreen
    out = io.StringIO()
    screen = PlainScreen(width=80, script=["look", "inventory", "examine me", "north",
                                           "south", "east", "west", "up"], out=out)
    for _ in range(8):
        screen.print("Please respond yes or no. > ")
        screen.read_line(80)
    screen.print("Please respond yes or no. > ")
    screen.flush()
    lines = out.getvalue().splitlines()
    assert all(line.startswith("Please respond yes or no. >") for line in lines), lines
    assert screen.lower_cursor[1] == len("Please respond yes or no. > ")
