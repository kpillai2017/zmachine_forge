"""TAKE ALL and friends: several objects in one command (ADR-035, ADR-036).

The expectations were checked against the real Inform 7 Advent (the
i7-advent-differential eval case plays the same commands on both builds) -
except where a test says otherwise: Advent has no two things of one name to
ask "Which do you mean" about, and nothing to wear.
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
    """What the game printed for one command (up to the next prompt) - also
    for an answer typed at a question's prompt, echoed as '> gold'."""
    for echo in (">" + command + "\n", "> " + command + "\n"):
        if echo in transcript:
            part = transcript.split(echo, 1)[1]
            return part.split("\n>", 1)[0].strip()
    raise AssertionError(f"{command!r} is not in the transcript")


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


# --- ADR-036: the second object, unclear items in a list, worn things

WARDROBE = """"Wardrobe" by Tester

The Lab is a room. A table is a supporter in the Lab. The table is fixed in place.
A box is an open container in the Lab.
The player wears a cloak. The player carries a hat. The hat is wearable.
A gold coin is in the Lab. A silver coin is in the Lab. A lamp is in the Lab.
"""


def test_the_second_object_is_always_one_thing():
    # as in the real Advent: 'You can only unlock the grate with one thing at a time.'
    t = run(["put lamp in all", "put lamp in box and table", "put lamp in box, table"],
            WARDROBE)
    for c in ("put lamp in all", "put lamp in box and table", "put lamp in box, table"):
        assert reply(t, c) == "You can't use multiple objects with that verb."


def test_parser_command_so_far_names_the_first_object_and_the_prepositions():
    body = WARDROBE + ("Rule for printing a parser error when the latest parser error "
                       "is the can't use multiple objects error:\n"
                       '\tsay "You can only [parser command so far] one thing at a time."\n')
    t = run(["put lamp in all", "x lamp and hat", "put all in all"], body)
    assert reply(t, "put lamp in all") == "You can only put the lamp in one thing at a time."
    assert reply(t, "x lamp and hat") == "You can only examine one thing at a time."
    # PUT ALL takes several: the trouble is the second object, and the first is
    # 'those things' (as in the real Advent's 'drop those things in what?')
    assert reply(t, "put all in all") == "You can only put those things in one thing at a time."


def test_the_higher_ranked_error_of_all_rows_is_reported():
    # PUT X ON Y reads 'lamp in all' as one name ('can't see'); PUT X IN Y
    # refuses ALL: Inform keeps the higher-ranked error, whatever the order
    t = run(["put lamp in all"], WARDROBE)
    assert reply(t, "put lamp in all") != "You can't see any such thing."


def test_which_do_you_mean_inside_a_list():
    # not checked against a real game (see the docstring): the question is
    # the one for a single object, asked once the whole command is read
    t = run(["take lamp and coin", "gold", "look"], WARDROBE)
    assert reply(t, "take lamp and coin") == \
        "Which do you mean, the gold coin or the silver coin?"
    assert reply(t, "gold") == "lamp: Taken.\ngold coin: Taken."
    t = run(["take coin and lamp", "silver", "take coin and coin", "gold"], WARDROBE)
    assert reply(t, "silver") == "silver coin: Taken.\nlamp: Taken."


def test_two_unclear_items_are_asked_about_in_turn():
    t = run(["take coin and coin", "gold", "silver"], WARDROBE)
    assert reply(t, "gold") == "Which do you mean, the gold coin or the silver coin?"
    assert reply(t, "silver") == "gold coin: Taken.\nsilver coin: Taken."


def test_the_reply_can_cancel_or_be_a_new_command():
    t = run(["take lamp and coin", "", "take lamp and coin", "look"], WARDROBE)
    assert "I beg your pardon?" in t
    assert "You can see a table, a box (empty), a gold coin, a silver coin and a lamp here." in \
        reply(t, "look")                                 # 'look' ran; nothing was taken


def test_except_takes_out_every_thing_the_name_fits():
    t = run(["take all but coin"], WARDROBE)
    assert reply(t, "take all but coin") == "box: Taken.\nlamp: Taken."


def test_all_and_a_named_thing_is_a_list():
    # one thing for ALL, and the lamp: a list, not '(the ...)' for one of them
    # (ALL lists what is carried in inventory order: the lamp, taken last, first)
    t = run(["take lamp", "drop all and lamp"], WARDROBE)
    assert reply(t, "drop all and lamp") == "lamp: Dropped.\nhat: Dropped."


def test_a_worn_thing_is_taken_off_first():
    # the words are those of the real Advent's story file (Inform 7 6L38's
    # can't drop / put / insert clothes being worn rules)
    t = run(["drop cloak", "wear cloak", "put cloak on table", "take cloak", "wear cloak",
             "put cloak in box"], WARDROBE)
    assert reply(t, "drop cloak") == "(first taking the cloak off)\nDropped."
    assert reply(t, "put cloak on table") == \
        "(first taking the cloak off)\nYou put the cloak on the table."
    assert reply(t, "put cloak in box") == \
        "(first taking the cloak off)\nYou put the cloak into the box."


def test_all_never_means_a_worn_thing():
    t = run(["drop all", "i"], WARDROBE)
    # the cloak is left out, but it is one of the things ALL could have meant
    # (as a held lamp is for TAKE ALL in the real Advent): a list, not '(the hat)'
    assert reply(t, "drop all") == "hat: Dropped."
    assert "a cloak (being worn)" in reply(t, "i")


def test_an_internal_rules_response_has_no_line_break_of_its_own():
    body = WARDROBE + """The yes or no question internal rule response (A) is "Yes or no? ".
Instead of waiting:
\tif the player consents:
\t\tsay "Wheee.";
\totherwise:
\t\tsay "Fine."
"""
    t = run(["wait", "maybe", "no"], body)
    assert "Yes or no? > no" in t
    t = run(["wait", "maybe", "yes"],
            WARDROBE + 'Instead of waiting: if the player consents, say "Wheee.".\n')
    assert "Please answer yes or no.> yes" in t


# --- checked against a second real game, Cold Iron (Inform 7 6G60, ADR-037)

TABLE_ROOM = """"Table" by Test

The Hall is a room.
The table is a supporter in the Hall. The book is on the table.
The tray is a portable supporter in the Hall.
"""


def test_a_supporter_is_fixed_in_place_unless_said_otherwise():
    t = run(["take table", "take tray"], TABLE_ROOM)
    assert reply(t, "take table") == "That's fixed in place."
    assert reply(t, "take tray") == "Taken."


def test_take_all_reaches_what_lies_on_a_supporter():
    room = TABLE_ROOM.replace("The tray is a portable supporter in the Hall.\n", "")
    t = run(["take all", "drop all", "take all"], room)
    first, second = t.split(">take all\n")[1:3]
    assert first.startswith("book: Taken.")    # off the table; the fixed table
    assert second.startswith("book: Taken.")   # still counts, so it is a list
