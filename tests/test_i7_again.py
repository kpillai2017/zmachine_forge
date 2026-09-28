"""AGAIN (or G) in Inform 7 games: the last command typed, typed again.

What each case should print was checked against the real Bronze (release
11), which runs in zforge: nothing to repeat gives "You can hardly repeat
that."; a command that failed is repeated too; G never repeats itself.
"""
from zforge.compiler.i7.driver import compile_i7
from zforge.vm.headless import play

STORY = '"Again" by Test\n\nThe Hall is a room. The lamp is in the Hall.\n'


def played(commands):
    return play(compile_i7(STORY, "t.ni", 8).story, commands).transcript


def replies(commands):
    """The reply to each command, in order: the text after each prompt's
    echoed command, up to the next prompt."""
    return [chunk.partition("\n")[2].strip() for chunk in played(commands).split("\n>")[1:]]


def test_again_with_nothing_to_repeat():
    assert replies(["g"])[0] == "You can hardly repeat that."


def test_g_and_again_repeat_the_last_command():
    r = replies(["x lamp", "g", "again"])
    assert r[0] == r[1] == r[2] == "You see nothing special about the lamp."


def test_again_repeats_a_command_that_failed():
    r = replies(["xyzzy", "g"])
    assert r[0] == r[1] == "That's not a verb I recognise."


def test_again_does_not_repeat_itself():
    r = replies(["take lamp", "g", "g"])
    assert r[0] == "Taken."
    assert r[1] == r[2] == "You already have that."


def test_again_takes_no_turn_when_there_is_nothing_to_repeat():
    # like a parser error; a repeated command takes its turn as usual
    story = STORY + ("The count is a number that varies.\nEvery turn:\n\tincrease the count by 1.\n"
                     "Counting is an action applying to nothing.\n"
                     "Understand \"count\" as counting.\n"
                     'Carry out counting: say "Turns so far: [count]."\n')
    out = play(compile_i7(story, "t.ni", 8).story, ["g", "count", "wait", "g", "count"]).transcript
    assert "Turns so far: 0." in out           # the first G took no turn
    assert "Turns so far: 3." in out           # count, wait and its repeat each took one
