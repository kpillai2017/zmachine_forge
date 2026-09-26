"""The I7-lite compiler: sentences, texts, the world model, and a story."""

import pytest

from zforge.compiler.i7.driver import compile_i7, generate_zil
from zforge.compiler.i7.model import build_model
from zforge.compiler.i7.problems import I7Problem, Problems
from zforge.compiler.i7.source import read_sentences, strip_comments
from zforge.compiler.i7.text import IfText, Literal, OneOf, Substitution, ends_sentence, \
    parse_text
from zforge.vm.headless import play

HELLO = '''"Hello World" by "A Student"
The Lab is a room. "A small, tidy lab."
When play begins: say "Hello, world!"
'''


def model_of(src):
    problems = Problems("t.ni")
    m = build_model(read_sentences(src), problems)
    return m, problems.messages


# ------------------------------------------------------------------ source
def test_comments_are_blanked_but_substitutions_kept():
    text = strip_comments('A [comment\nover two lines] "say [the noun]"')
    assert "comment" not in text and "[the noun]" in text
    assert text.count("\n") == 1                     # line numbers survive


def test_sentences_end_at_full_stops_and_at_quoted_sentences():
    ss = read_sentences('The Lab is a room. "A tidy lab." The Bar is a room.')
    assert [s.text for s in ss] == ["The Lab is a room.", '"A tidy lab."', "The Bar is a room."]


def test_rule_bodies_keep_their_phrases_and_indentation():
    ss = read_sentences("Instead of taking the lamp:\n\tsay \"No.\";\n\tstop the action.\n")
    rule = ss[0]
    assert rule.is_rule and rule.text == "Instead of taking the lamp:"
    assert [(b.indent, b.text) for b in rule.body] == [(1, 'say "No.";'), (1, "stop the action.")]


# ------------------------------------------------------------------ text
def test_text_substitutions_ifs_and_one_of():
    t = parse_text('"It is [the noun][if x], dim[otherwise] bright[end if]; '
                   '[one of]a[or]b[cycling]."')
    kinds = [type(p) for p in t.parts]
    assert kinds == [Literal, Substitution, IfText, Literal, OneOf, Literal]
    assert t.parts[4].mode == "cycling"


def test_single_quotes_become_double_except_apostrophes():
    t = parse_text('''"'Hi,' she said. Don't."''')
    assert t.parts[0].text == '"Hi," she said. Don\'t.'


def test_a_text_ending_in_punctuation_ends_a_sentence():
    assert ends_sentence(parse_text('"Hello!"'))
    assert not ends_sentence(parse_text('"Hello"'))
    assert not ends_sentence(parse_text('"Hello [the noun]"'))


# ------------------------------------------------------------------ model
def test_world_model_rooms_map_things_and_shortened_names():
    m, problems = model_of('''
The Foyer of the Opera House is a room. The Cloakroom is west of the Foyer.
The Bar is south of the Foyer. The Bar is dark.
The small brass hook is a scenery supporter in the Cloakroom. Understand "peg" as the hook.
The player wears a velvet cloak.
''')
    assert problems == []
    assert m.map[("Foyer of the Opera House", "west")] == "Cloakroom"
    assert m.map[("Cloakroom", "east")] == "Foyer of the Opera House"     # both ways
    assert "LITBIT" in m.objects["Bar"].unflags
    hook = m.objects["small brass hook"]
    assert (hook.kind, hook.parent, "SCENERYBIT" in hook.flags, hook.words) == \
        ("supporter", "Cloakroom", True, ["peg"])
    cloak = m.objects["velvet cloak"]
    assert (cloak.parent, cloak.relation) == ("yourself", "worn")


def test_problems_quote_the_sentence_and_its_line():
    _, problems = model_of("The Lab is a room.\nThe lamp is on the Lab.\n")
    assert problems
    assert problems[0].startswith("t.ni:2: Problem. You wrote 'The lamp is on the Lab.'")
    assert "not a supporter" in problems[0]


def test_unknown_sentences_are_problems_not_crashes():
    with pytest.raises(I7Problem, match="does not understand"):
        generate_zil("The Lab is a room.\nThe Lab frobnicates wildly.\n")


# ------------------------------------------------------------------ stories
@pytest.mark.parametrize("target", [5, 7, 8])
def test_hello_world_plays_on_every_target(target):
    story = compile_i7(HELLO, "hello.ni", target).story
    assert story[0] == target
    text = play(story, ["look", "wait", "quit", "y"]).transcript
    assert text.startswith("Hello, world!")
    assert "Hello World\nAn Interactive Fiction by A Student" in text
    assert "Lab\nA small, tidy lab." in text and "Time passes." in text


def test_the_default_target_is_z8():
    assert compile_i7(HELLO, "hello.ni").version == 8


def test_generated_zil_names_its_source_sentences():
    _, zil, _ = generate_zil(HELLO, "hello.ni")
    assert '<ROUTINE RULE-1 ()   ;"when play begins (line 3)"' in zil
    assert '<INSERT-FILE "lib/i7/runtime">' in zil


def test_the_title_line_needs_no_full_stop_or_blank_line():
    ss = read_sentences('"Hello" by "Me"\nThe Lab is a room.')
    assert [s.text for s in ss] == ['"Hello" by "Me"', "The Lab is a room."]


# ------------------------------------------------------------------ Cloak mechanics
def test_one_line_rules_use_a_comma():
    ss = read_sentences('Instead of taking the lamp, say "No."')
    assert ss[0].text == "Instead of taking the lamp:" and ss[0].body[0].text == 'say "No."'


CLOAKROOM = '''"Test" by "T"
The Hall is a room. The Bar is south of the Hall. The Bar is dark.
The player carries a lamp.
Before doing something other than going in the Bar when in darkness:
	say "Careful!" instead.
'''


def test_out_of_world_actions_skip_before_rules():
    text = play(compile_i7(CLOAKROOM, "t.ni").story, ["s", "score", "wait"]).transcript
    after_s = text.split(">s", 1)[1]
    assert "There is no score in this story." in after_s        # score: no "Careful!"
    assert after_s.count("Careful!") == 1                        # only wait


def test_a_held_thing_is_matched_once_with_the_player_in_the_room():
    text = play(compile_i7(CLOAKROOM, "t.ni").story, ["x lamp"]).transcript
    assert "Which do you mean" not in text and "You see nothing special about the lamp." in text


# ------------------------------------------------------------------ 7b

def test_names_with_of_are_not_properties():
    m, problems = model_of('The set of keys is in the Lab. The Lab is a room.')
    assert problems == []
    assert m.objects["set of keys"].parent == "Lab"


def test_a_door_has_two_sides_and_a_key():
    m, problems = model_of('The Top is a room. The Bottom is a room. The grate is a door. '
              'It is below the Top and above the Bottom. The grate is locked. '
              'The key is in the Top. The key unlocks the grate.')
    assert problems == []
    grate = m.objects["grate"]
    assert grate.sides == [("Top", "down"), ("Bottom", "up")]
    assert grate.key == "key" and "LOCKEDBIT" in grate.flags


def test_kind_defaults_with_usually():
    m, problems = model_of('A room is usually dark. A forest is a kind of room. '
              'The printed name of a forest is usually "Forest". The Wood is a forest.')
    assert problems == []
    assert "LITBIT" in m.kinds["room"].unflags and m.kinds["forest"].printed == "Forest"


def test_naming_articles_and_synonyms():
    m, problems = model_of(
              'The Lab is a room. The lamp is a device in the Lab. The lamp is privately-named. '
              'The printed name of the lamp is "brass lantern". The water is in the Lab. '
              'The indefinite article of the water is "some". Understand "lantern" as the lamp. '
              'Understand "plugh" as north. Understand the command "grab" as "take".')
    assert problems == []
    lamp, water = m.objects["lamp"], m.objects["water"]
    assert lamp.private and lamp.printed == "brass lantern" and lamp.words == ["lantern"]
    assert water.article == "some"
    assert m.direction_words == {"north": ["plugh"]} and m.command_synonyms == [("grab", "take")]


def test_privately_named_things_are_not_understood_by_their_name():
    zil = compile_i7('"T" by "U"\nThe Lab is a room. The lamp is a device in the Lab. '
                     'The lamp is privately-named. Understand "lantern" as the lamp.', "t.ni").zil
    obj = zil[zil.index("<OBJECT LAMP"):]
    assert "(SYNONYM LANTERN)" in obj[:obj.index(">")]
