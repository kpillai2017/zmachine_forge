"""Words a player can type, and grammar lines with several fixed words.

Three bugs found while writing examples/crusoe.ni (ADR-062):

* a grammar line with two fixed words in a row and no object, such as
  "write in journal", gave an internal error instead of working;
* a name's possessive word ("the cook's pot") could not be typed;
* the word "of" in a name ("the bag of shot") could not be typed.
"""
import pytest

from zforge.compiler.driver import compile_zil
from zforge.compiler.i7.driver import compile_i7
from zforge.compiler.i7.problems import I7Problem
from zforge.vm.headless import play

HEAD = '"Test" by Tester\n\nThe Galley is a room.\n\n'


def run(body: str, commands: list[str]) -> str:
    story = compile_i7(HEAD + body, "test.ni", target=8).story
    t = play(story, commands).transcript
    return t[t.index(">"):]


def problem_of(body: str) -> str:
    with pytest.raises(I7Problem) as e:
        compile_i7(HEAD + body, "test.ni", target=8)
    return str(e.value)


# ------------------------------------------------ grammar lines


TWO_WORDS = """Writing is an action applying to nothing.
Understand "write in journal" and "keep a diary" as writing.
Carry out writing: say "You write up the day."
Circling is an action applying to nothing.
Understand "swim round ship" as circling.
Carry out circling: say "You swim round the ship."
"""


def test_two_fixed_words_with_no_object_play():
    t = run(TWO_WORDS, ["write in journal", "keep a diary", "swim round ship"])
    assert t.count("You write up the day.") == 2
    assert "You swim round the ship." in t


def test_the_first_word_alone_does_not_match_a_two_word_line():
    t = run(TWO_WORDS, ["write in"])
    assert "You write up the day." not in t


@pytest.mark.parametrize("line", [
    "fill [something] with water",           # two words after one object
    "look carefully at [something]",         # two words before an object
    "put [something] into the [something]",  # two words between objects
    "row out to the ship",                   # four words, no object
])
def test_a_line_the_grammar_table_cannot_hold_is_a_problem_not_a_crash(line):
    body = ("Fiddling is an action applying to one thing.\n" if line.count("[") == 1
            else "Fiddling is an action applying to two things.\n" if "[" in line
            else "Fiddling is an action applying to nothing.\n")
    message = problem_of(body + f'Understand "{line}" as fiddling.\n')
    assert "internal error" not in message
    assert line in message
    assert "more fixed words in a row" in message


def test_the_librarys_own_lines_with_options_still_fit():
    # "put [things preferably held] in [something]" keeps an option list,
    # stored as two tokens; the capacity check must not count it as words.
    t = run("A coin is in the Galley. A bowl is a container in the Galley.",
            ["take coin", "put coin in bowl"])
    assert "You put the coin into the bowl." in t


# ------------------------------------------------ possessives and "of"


def test_a_possessive_word_can_be_typed():
    t = run("The cook's pot is in the Galley. The boatswain's whistle is in the Galley.",
            ["x cook's pot", "x cook's", "x boatswain's whistle"])
    assert "You can't see any such thing." not in t
    assert t.count("You see nothing special about the cook's pot.") == 2
    assert "You see nothing special about the boatswain's whistle." in t


def test_of_in_a_name_can_be_typed():
    t = run("The bag of shot is in the Galley. The roll of sailcloth is in the Galley.",
            ["x bag of shot", "take roll of sailcloth", "x bag"])
    assert "You can't see any such thing." not in t
    assert "You see nothing special about the bag of shot." in t
    assert "Taken." in t


# ------------------------------------------------ the ZIL side


def test_zil_an_escaped_character_in_an_atom_loses_its_backslash():
    from zforge.asm.info import dictionary_report
    src = ('<VERSION 5>\n<OBJECT PAN (DESC "cook\'s pan") (SYNONYM COOK\\\'S PAN)>\n'
           '<ROUTINE GO () <QUIT>>\n')
    words = dictionary_report(compile_zil(src, "t.zil", 5).story)
    assert "cook's" in words
    assert "cook\\" not in words


def test_zil_syntax_with_two_particles_and_no_object():
    from tests.test_grammar import desugared, show, syntax_rows
    program, d = desugared("<SYNTAX WRITE IN JOURNAL = V-WRITE>\n<ROUTINE V-WRITE () <RTRUE>>")
    (row,) = syntax_rows(program)
    shown = [show(item) for item in row]
    assert "in" in shown and "journal" in shown


# ------------------------------------------- 5. a CONSTANT may be a table (§6.2)
def test_a_zil_constant_can_be_a_table():
    zil = ('<VERSION 5>\n<CONSTANT PRIMES <TABLE 2 3 5 7>>\n'
           '<ROUTINE GO () <PRINTN <GET ,PRIMES 2>> <PRINTN <GET ,PRIMES 3>> <CRLF> <QUIT>>\n')
    story = compile_zil(zil, "t.zil").story
    assert "57" in play(story, []).transcript


def test_many_actions_do_not_run_out_of_globals():
    # every action has a rulebook; they are table constants, not globals, so a
    # story with far more actions than the 240 globals still compiles and plays
    # (the command words use letters only: a digit costs two of a
    # dictionary word's nine characters, so "frob249" would be cut short)
    words = [a + b for a in "abcdefghijklmnopqrstuvwxyz" for b in "abcdefghij"][:250]
    body = "".join(
        f'Frobbing{i} is an action applying to nothing. Understand "zz{w}" as frobbing{i}.\n'
        f'Carry out frobbing{i}: say "Frob {i}!"\n' for i, w in enumerate(words))
    out = run(body, ["zz" + words[7], "zz" + words[249]])
    assert "Frob 7!" in out and "Frob 249!" in out
