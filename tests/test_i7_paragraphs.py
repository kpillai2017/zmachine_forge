"""Blank lines, as the real Bronze (built by Inform 7) prints them."""
from zforge.compiler.i7.driver import compile_i7
from zforge.vm.headless import play

STORY = ('"T" by T\n\n'
         'The Hall is a room. "A plain hall."\n'
         'The Yard is north of the Hall. "A bare yard."\n'
         'A sign is in the Hall. The description of the sign is "Painted letters."\n'
         'After examining the sign, say "It says: KEEP OUT."\n'
         'To say old times: say "You remember old times."\n'
         'The Cellar is south of the Hall. "Damp.[paragraph break][old times]"\n')


def transcript(commands: list[str]) -> str:
    return play(compile_i7(STORY, "t.ni", 8).story, commands).transcript


def test_two_rules_output_is_set_apart_by_a_blank_line():
    assert "Painted letters.\n\nIt says: KEEP OUT.\n\n>" in transcript(["x sign"])


def test_going_sets_off_the_room_heading_but_looking_does_not():
    out = transcript(["north", "look"])
    assert ">north\n\nYard\n" in out
    assert ">look\nYard\n" in out


def test_a_description_that_ends_its_own_line_gets_no_extra_blank_line():
    out = transcript(["south"])
    assert "Damp.\n\nYou remember old times.\n\n>" in out
    assert "old times.\n\n\n>" not in out
