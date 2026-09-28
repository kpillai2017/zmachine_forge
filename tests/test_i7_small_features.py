"""Small features Cold Iron needs (ADR-052): a property of one thing, 'is not
<adjective>', the attacking and entering actions, Understand ... as a mistake."""
from zforge.compiler.i7.driver import compile_i7
from zforge.vm.headless import play

STORY = '''"Small" by Test

The Hall is a room. A table is a supporter in the Hall. A book is on the table.
The lamp is in the Hall. The lamp has a number called the charge. The charge is 3.
The lamp can be polished. The lamp is not polished.
Rubbing is an action applying to one thing. Understand "rub [something]" as rubbing.
Carry out rubbing:
\tincrease the charge of the lamp by 1;
\tnow the lamp is polished;
\tsay "Charge [charge of the lamp][if the lamp is polished], polished[end if]."
Understand "help" as a mistake ("(No help: only [the lamp].)").
Understand "polish [something]" as a mistake ("You can't polish [the noun].").
Every turn: say "(a turn)".
'''


def replies(commands: list[str]) -> list[str]:
    out = play(compile_i7(STORY, "small.ni", 8).story, commands).transcript
    chunks = [chunk.partition("\n")[2] for chunk in out.split("\n>")[1:]][:len(commands)]
    return [" ".join(chunk.split()) for chunk in chunks]


def test_a_property_of_one_thing_and_not_an_adjective():
    assert replies(["rub lamp"]) == ["Charge 4, polished. (a turn)"]


def test_attacking_as_the_real_library_says_it():
    r = replies(["attack book", "break book", "hit table", "smash table", "punch table",
                 "destroy book", "thump table"])
    assert set(r) == {"Violence isn't the answer to this one. (a turn)"}


def test_entering_names_the_verb():
    r = replies(["enter book", "get in book", "get onto table", "sit on table",
                 "sit inside table", "stand on table"])
    assert r[:3] == ["That's not something you can enter. (a turn)"] * 3
    assert r[3:5] == ["That's not something you can sit down on. (a turn)"] * 2
    assert r[5] == "That's not something you can stand on. (a turn)"


def test_a_mistake_says_its_text_and_takes_no_turn():
    assert replies(["help", "polish book"]) == ["(No help: only the lamp.)",
                                                "You can't polish the book."]
