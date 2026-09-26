"""TAKE ALL and friends: several objects in one command (ADR-035).

Every expectation here was checked against the real Inform 7 Advent (the
i7-advent-differential eval case plays the same commands on both builds).
"""

from zforge.compiler.driver import compile_zil
from zforge.compiler.i7.driver import compile_i7
from zforge.vm.headless import play

LAB = """"All" by Tester

The Lab is a room. A brass lamp is in the Lab. Some keys are in the Lab.
A heavy desk is in the Lab. The desk is fixed in place.
A chart is scenery in the Lab. A box is a container in the Lab.
Bob is a man in the Lab. The player wears a cloak.
"""


def run(commands: list[str], body: str = LAB) -> str:
    story = compile_i7(body, "t.ni", target=8).story
    t = play(story, commands).transcript
    return t[t.find(">"):]


def reply(transcript: str, command: str) -> str:
    """What the game printed for one command (up to the next prompt)."""
    part = transcript.split(">" + command + "\n", 1)[1]
    return part.split("\n>", 1)[0].strip()


def test_take_all_takes_what_lies_in_the_room_in_order():
    t = run(["take all"])
    assert reply(t, "take all") == "brass lamp: Taken.\nkeys: Taken.\nbox: Taken."


def test_all_leaves_out_fixed_scenery_people_and_worn_things():
    t = run(["take all", "drop all"])
    assert "desk" not in reply(t, "take all")        # fixed in place
    assert "chart" not in reply(t, "take all")       # scenery
    assert "Bob" not in reply(t, "take all")         # a person
    assert "cloak" not in reply(t, "drop all")       # worn
    assert reply(t, "drop all") == "box: Dropped.\nkeys: Dropped.\nbrass lamp: Dropped."


def test_except_but_and_lists():
    t = run(["take all but lamp", "drop all except box", "take lamp and keys", "drop lamp, keys"])
    assert reply(t, "take all but lamp") == "keys: Taken.\nbox: Taken."
    # held: keys, box and the worn cloak - three could be meant, so a list of one
    assert reply(t, "drop all except box") == "keys: Dropped."
    assert reply(t, "take lamp and keys") == "brass lamp: Taken.\nkeys: Taken."
    assert reply(t, "drop lamp, keys") == "brass lamp: Dropped.\nkeys: Dropped."


def test_all_is_one_object_only_when_one_thing_could_be_meant():
    # held: only the keys and the worn cloak... two candidates, so a list of one
    t = run(["take keys", "drop all"])
    assert reply(t, "drop all") == "keys: Dropped."
    # nothing worn: the keys are the only thing held - one object, '(the keys)'
    t = run(["take keys", "drop all"], LAB.replace(" The player wears a cloak.", ""))
    assert reply(t, "drop all") == "(the keys)\nDropped."
    # TAKE ALL with one thing left: what is held could be meant too - a list
    t = run(["take lamp", "take keys", "take all"])
    assert reply(t, "take all") == "box: Taken."


def test_put_all_in_the_box_leaves_out_the_box():
    t = run(["take all", "put all in box"])
    assert reply(t, "put all in box") == (
        "keys: You put the keys into the box.\nbrass lamp: You put the brass lamp into the box.")


def test_the_two_errors_of_several_objects():
    t = run(["x all", "take all", "take all"])
    assert reply(t, "x all") == "You can't use multiple objects with that verb."
    assert t.count("There are none at all available!") == 1   # the second TAKE ALL


def test_a_list_is_for_one_command_only():
    t = run(["take all", "look"])
    assert reply(t, "look").startswith("Lab\n")                # not once per object


def test_an_unknown_word_in_a_list():
    t = run(["take lamp and zork"])
    assert reply(t, "take lamp and zork") == "You can't see any such thing."


def test_an_authors_things_token():
    t = run(["steal all"], LAB + '\nUnderstand "steal [things]" as taking.\n')
    assert reply(t, "steal all") == "brass lamp: Taken.\nkeys: Taken.\nbox: Taken."


def test_dropping_what_is_already_here():
    t = run(["drop lamp"])
    assert reply(t, "drop lamp") == "The brass lamp is already here."


def test_zil_games_have_no_all():
    """ALL is Inform 7's: the ZIL parser (same lib/parser.zil) is unchanged."""
    from pathlib import Path
    src = Path("examples/cloak_syntax.zil")
    t = play(compile_zil(src.read_text(), str(src)).story, ["take all", "take cloak and hook"])
    assert 'I don\'t know the word "all".' in t.transcript
    assert 'I don\'t know the word "and".' in t.transcript
