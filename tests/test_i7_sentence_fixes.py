"""Fixes for five ways the I7-lite compiler misread sentences.

Each was found while rewriting Emily Short's "Bronze" in I7-lite. Before the
fixes, every one of them built a story without complaint, and the story then
misbehaved (or, in the case of the attribute limit, stopped with an internal
error). The tests here use tiny stories that recreate each case.
"""

import pytest

from zforge.compiler.i7.driver import compile_i7
from zforge.compiler.i7.model import build_model
from zforge.compiler.i7.problems import I7Problem, Problems
from zforge.compiler.i7.source import read_sentences
from zforge.vm.headless import play


def model_of(src):
    problems = Problems("t.ni")
    m = build_model(read_sentences(src), problems)
    return m, problems.messages


def played(src, commands):
    return play(compile_i7(src, "t.ni", 8).story, commands).transcript


# ------------------------------------------------ 1. one thing, two places
def test_a_short_name_that_means_an_existing_thing_cannot_move_it():
    # 'the inkpot' is a shortening of the only name containing 'inkpot', so
    # the second sentence tried to move the history into the Black Gallery.
    m, problems = model_of('The Records Room is a room. The history of the inkpot is '
                           'scenery in the Records Room.\n'
                           'The Black Gallery is east of the Records Room. '
                           'The inkpot is in the Black Gallery.\n')
    assert len(problems) == 1
    assert "already in 'Records Room'" in problems[0]
    assert "give it a name that is not part of 'history of the inkpot'" in problems[0]
    assert m.find("history of the inkpot").parent == "Records Room"      # not moved


def test_saying_the_same_place_twice_is_not_a_contradiction():
    m, problems = model_of('The Lab is a room. The lamp is in the Lab. The lamp is in the Lab.')
    assert problems == [] and m.find("lamp").parent == "Lab"


# ------------------------------------------------ 2. keywords inside quotes
KEY = ('The Lab is a room. The small key is in the Lab. The description of the small key '
       'is "A key intended to unlock more than one thing[if the small key is in the Lab], '
       'lying here[end if]."\nThe box is a locked container in the Lab. '
       'The small key unlocks the box.\n')


def test_a_keyword_inside_quoted_text_does_not_make_a_different_sentence():
    # 'unlock' in the description once made this a key sentence, cutting the
    # description in two.
    m, problems = model_of(KEY)
    assert problems == [] and m.find("box").key == "small key"
    out = played(KEY, ["x key", "unlock box with key"])
    assert "A key intended to unlock more than one thing, lying here." in out
    assert "You unlock the box." in out


def test_quoted_text_still_reaches_the_sentence_that_owns_it():
    src = ('The Lab is a room. The lamp is in the Lab. '
           'The printed name of the lamp is "lamp north of the Lab".')
    assert model_of(src)[1] == []
    assert "You can see a lamp north of the Lab here." in played(src, ["look"])


# ------------------------------------------------------- 3. map sentences
def links(m):
    return {(a, d): b for (a, d), b in m.map.items()}


def test_it_after_a_room_means_that_room():
    # 'It' once created a room called 'It'.
    m, problems = model_of('The Hall is a room. The Library is north of the Hall. '
                           'It is west of the Garden.\nThe Garden is a room.')
    assert problems == [] and "It" not in {o.name for o in m.rooms()}
    assert links(m)[("Garden", "west")] == "Library"
    assert links(m)[("Library", "east")] == "Garden"


def test_it_that_is_not_a_room_is_a_problem():
    m, problems = model_of('The Hall is a room. The lamp is in the Hall. It is north of the Hall.')
    assert len(problems) == 1 and "not clear which room 'It' means" in problems[0]


def test_directions_can_be_listed_with_commas():
    # The list once became one room called 'Crypt, southwest of the Fen'.
    m, problems = model_of('The Crypt is a room. The Fen is a room. The Moor is a room. '
                           'The Pit is south of the Crypt, southwest of the Fen and '
                           'southeast of the Moor.')
    assert problems == [] and len(m.rooms()) == 4
    assert links(m)[("Crypt", "south")] == "Pit" and links(m)[("Fen", "southwest")] == "Pit"
    assert links(m)[("Moor", "southeast")] == "Pit"


def test_a_plural_door_can_be_placed_with_they():
    m, problems = model_of('The Ground is a room. The Attic is a room. A staircase is a kind '
                           'of door. The steps are a staircase. They are above the Ground '
                           'and below the Attic.')
    assert problems == []
    assert m.find("steps").sides == [("Ground", "up"), ("Attic", "down")]


# ------------------------------------------------ 4. too many attributes
MANY = ["p" + chr(97 + i // 26) + chr(97 + i % 26) for i in range(40)]
MANY_SRC = ('The Lab is a room. The rock is in the Lab.\n'
            + "".join(f"A thing can be {p}.\n" for p in MANY)
            + "The rock is " + ", ".join(MANY) + ".\n")


def test_too_many_either_or_properties_is_a_problem_in_the_source():
    # This once said 'internal error ... a bug in zforge'.
    with pytest.raises(I7Problem) as e:
        compile_i7(MANY_SRC, "t.ni", 8)
    text = str(e.value)
    assert "internal error" not in text and "room for only 48" in text
    assert "A thing can be pba." in text          # the first one that did not fit
    assert "pba, pbb" in text and "number property" in text


def test_the_zil_compiler_reports_the_overflow_once():
    from zforge.common.errors import ZForgeError
    from zforge.compiler.driver import compile_zil
    flags = " ".join(f"F{i}BIT" for i in range(50))
    zil = f'<OBJECT ROCK (FLAGS {flags})>\n<ROUTINE GO () <QUIT>>\n'
    with pytest.raises(ZForgeError) as e:
        compile_zil(zil, "t.zil", 5)
    text = str(e.value)
    assert text.count("too many FLAGS") == 1
    assert "uses 50 attributes" in text and "F48BIT, F49BIT" in text


# ------------------------------------ 5. a bare text with a full stop after it
def test_a_room_description_ending_in_a_bracket_can_have_a_full_stop():
    # '"...[end if]".' was once printed with its quote marks and full stop.
    out = played('The Hall is a room. "A hall[if the Hall is lit], brightly lit[end if]".\n'
                 'The Cellar is below the Hall. "Damp and cold."',
                 ["look", "down"])
    assert "A hall, brightly lit" in out and '"A hall' not in out and 'lit".' not in out
    assert "Damp and cold." in out


# ------------------------------------ 6. trying an action no command asks for
def test_an_action_with_no_understand_line_can_be_tried():
    # It once had no action number, and the build stopped with an internal error.
    out = played("The Hall is a room. The Kitchen is north of the Hall.\n"
                 "Looking toward is an action applying to one thing.\n"
                 'Carry out looking toward: say "You make out [the noun] that way."\n'
                 "Waving about is an action applying to nothing.\n"
                 'Carry out waving about: say "You wave."\n'
                 "Instead of waiting: try looking toward the Kitchen; try waving about.",
                 ["wait"])
    assert "You make out the Kitchen that way." in out and "You wave." in out


# ------------------------------------ 7. "silently try", in either order
def test_silently_try_works_in_both_orders():
    out = played("The Hall is a room. The lamp is in the Hall.\n"
                 "Instead of waiting: silently try taking the lamp; say \"Have it: "
                 "[if the player carries the lamp]yes[otherwise]no[end if].\"\n"
                 'Instead of looking: try silently dropping the lamp; say "Put down."',
                 ["wait", "look", "inventory"])
    assert "Have it: yes." in out and "Put down." in out and "carrying nothing" in out
    assert "Taken." not in out and "Dropped." not in out      # silently: no reports
