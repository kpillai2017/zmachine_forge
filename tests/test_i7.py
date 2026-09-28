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


# ------------------------------------------------------------------ 7c

def test_third_person_singular_of_the_storys_verbs():
    from zforge.compiler.i7.model import third_person_singular as s
    assert [s(v) for v in ("flow", "reach", "carry", "go", "have", "play", "fix")] == \
        ["flows", "reaches", "carries", "goes", "has", "plays", "fixes"]


def test_adaptive_text_lowers_to_agreement_routines():
    zil = compile_i7('"T" by "U"\nTo flow is a verb. The Lab is a room. '
                     '"[We] [are] here. [regarding the lamp][They] [flow]." '
                     'The lamp is in the Lab.', "t.ni").zil
    assert '<SAY-WE "You">' in zil and '<SAY-VERB "are" "is">' in zil
    assert '<SETG PRIOR-NAMED ,LAMP>' in zil and '<SAY-VERB "flow" "flows">' in zil


def test_a_short_name_that_means_an_existing_room_is_a_problem():
    m, problems = model_of("The Stream Bank is a room. The stream is scenery in the Stream Bank.")
    assert len(problems) == 1 and "inside itself" in problems[0]


# ------------------------------------------------------------------ rule swapping
def played(src, commands, target=8):
    return play(compile_i7(src, "t.ni", target).story, commands).transcript


LAB = 'The Lab is a room. "A small lab." The statue is scenery in the Lab. '


def test_a_library_rule_can_be_unlisted():
    src = LAB + "The can't take scenery rule is not listed in the check taking rulebook."
    assert "Taken." in played(src, ["take statue"])
    assert "That's hardly portable." in played(LAB, ["take statue"])


def test_the_authors_rule_can_take_a_library_rules_place():
    src = LAB + ("The loud report rule is listed instead of the standard report taking rule "
                 "in the report taking rulebook.\nThe pebble is in the Lab.\n\n"
                 'This is the loud report rule:\n\tsay "You grab [the noun]!"\n')
    text = played(src, ["take pebble"])
    assert "You grab the pebble!" in text and "Taken." not in text


def test_a_response_can_be_edited_and_keeps_substitutions():
    src = LAB + ("The pebble is in the Lab. "
                 'The standard report taking rule response (A) is "[The noun]: got it."')
    assert "The pebble: got it." in played(src, ["take pebble"])


def test_unknown_rule_names_are_problems():
    src = LAB + 'The fly away rule response (A) is "Whee."'
    with pytest.raises(I7Problem) as e:
        compile_i7(src, "t.ni")
    assert "there is no rule called 'fly away rule'" in str(e.value)


def test_a_command_can_be_understood_as_something_new():
    src = LAB + ('Understand the command "take" as something new. Snatching is an action '
                 'applying to one thing. Understand "take [something]" as snatching.\n\n'
                 'Report snatching: say "Snatched!"')
    assert "Snatched!" in played(src, ["take statue"])


def test_rooms_have_their_properties_and_they_can_change():
    src = ('Every room has a number called the visit count. The Lab is a room.\n\n'
           'Every turn: increase the visit count of the location by 1; '
           'say "Turn [visit count of the location]."')
    text = played(src, ["wait", "wait"])
    assert "Turn 1." in text and "Turn 2." in text


def test_going_nowhere_and_the_door_gone_through():
    src = LAB + '\n\nBefore going nowhere: say "No exit there."'
    assert "No exit there." in played(src, ["north"])


def test_a_list_of_subjects_and_encloses():
    m, problems = model_of("The Lab is a room. The Hall is north of the Lab. "
                           "A room is usually dark. The Lab and the Hall are lighted.")
    assert problems == []
    assert "LITBIT" in m.objects["Lab"].flags and "LITBIT" in m.objects["Hall"].flags
    src = LAB + ('The box is a container in the Lab. The coin is in the box.\n\n'
                 'Every turn when the Lab encloses the coin: say "Coin here."')
    assert "Coin here." in played(src, ["wait"])


def test_rules_are_separated_by_a_blank_line_as_in_inform_7():
    src = LAB + ('The pebble is in the Lab.\n\nBefore taking the pebble: say "You reach down."'
                 '\n\nEvery turn: say "Tick."')
    text = played(src, ["take pebble"])
    assert "You reach down.\n\nTaken.\n\nTick.\n" in text


def test_spaces_are_kept_and_source_line_breaks_become_one_space():
    from zforge.compiler.i7.standard import zil_string
    assert zil_string("two  spaces") == '"two  spaces"'
    assert zil_string("across\n   lines") == '"across lines"'


def test_differential_responses_are_split_at_each_command():
    from eval.differential import differences, responses
    real = "Title\nBy X\n\nHello.\n\n>look\nLab\n\n>wait\nTime passes.\n\n>"
    ours = "Hello.\n\nTitle\nBy Y\n\n>look\nLab\n\n>wait\nNothing.\n\n>"
    banner = ["Title", "By .*"]
    r, o = responses(real, ["look", "wait"], banner), responses(ours, ["look", "wait"], banner)
    assert r[0] == o[0] == ["Hello.", ""] and r[1] == o[1] == ["Lab", ""]
    assert differences(["look", "wait"], r, o) == [
        "'>wait': Inform 7 printed 'Time passes.', we printed 'Nothing.'"]


def test_differential_catches_a_blank_line_too_many_before_the_prompt():
    from eval.differential import differences, responses
    real = ">wait\nTime passes.\n\n>"
    ours = ">wait\nTime passes.\n\n\n>"
    r, o = responses(real, ["wait"], []), responses(ours, ["wait"], [])
    assert differences(["wait"], r, o) == [
        "'>wait': Inform 7 printed nothing more, we printed a blank line"]


def test_every_library_rule_is_listed_in_the_docs():
    from pathlib import Path

    from zforge.compiler.i7.standard import ACTIONS, LIBRARY_RULES
    doc = (Path(__file__).parent.parent / "docs" / "I7_LITE.md").read_text()
    names = [r.name for a in ACTIONS for rules in a.rules.values() for r in rules]
    # 83: the carrying requirements rule serves three actions; one routine
    # serves the three clothes-being-worn rules, but each is a rule of its own;
    # the four actions on a topic have five; attacking and entering one each
    assert len(set(names)) == 83
    assert [n for n in LIBRARY_RULES if f"| {n} |" not in doc] == []   # internal ones too


# --- Advent's preliminary cave: Inform 7 behaviours checked against the real game

def _play_i7(src: str, commands: list[str]) -> str:
    return play(compile_i7(src, "t.ni", 8).story, commands).transcript


def test_comma_if_blocks_and_modal_verbs():
    text = _play_i7('''"T" by A

The Lab is a room. The rod is in the Lab. The bird is in the Lab.
To approach is a verb.

Check taking the bird:
	if the player carries the rod,
		say "[We] [approach] [it] and [we] [cannot catch] it." instead;
''', ["take rod", "take bird"])
    assert "You approach it and you cannot catch it." in text


def test_there_and_it_start_a_singular_agreement():
    text = _play_i7('''"T" by A

The Lab is a room. "[We] [are] here. [There] [are] a light. [We] [see] [it] [glow]."
To see is a verb. To glow is a verb.
''', [])
    assert "You are here. There is a light. You see it glows." in text


def test_are_makes_a_new_thing_plural_and_some_is_its_article():
    m, problems = model_of('''"T" by A

The Lab is a room. Some keys are in the Lab. A lamp is in the Lab.
''')
    assert problems == []
    assert "PLURALBIT" in m.objects["keys"].flags and m.objects["keys"].article == "some"
    assert "PLURALBIT" not in m.objects["lamp"].flags


def test_adjectives_before_the_kind_and_comma_placement():
    m, problems = model_of('''"T" by A

The Top is a room. Some steps are an open unopenable door, below the Top.
The Hall is west from the steps.
In the Top is a scenery, privately-named, plural-named thing called walls.
''')
    assert problems == []
    steps = m.objects["steps"]
    assert steps.kind == "door" and "OPENBIT" in steps.flags and "PLURALBIT" in steps.flags
    assert ("Top", "down") in steps.sides and ("Hall", "east") in steps.sides
    walls = m.objects["walls"]
    assert walls.private and walls.parent == "Top" and "PLURALBIT" in walls.flags


def test_nowhere_cancels_the_reverse_connection():
    m, problems = model_of('''"T" by A

The Crawl is a room. The Debris Room is inside from the Crawl. Outside is nowhere.
''')
    assert problems == []
    assert m.map[("Crawl", "inside")] == "Debris Room"
    assert ("Debris Room", "outside") not in m.map


def test_a_list_subject_can_come_before_its_rooms():
    m, problems = model_of('''"T" by A

The Lab and the Hall are lighted. The Hall is north of the Lab.
''')
    assert problems == []
    assert m.objects["Hall"].kind == "room" and "LITBIT" in m.objects["Hall"].flags


def test_move_the_player_describes_unless_asked_not_to():
    src = '''"T" by A

The Lab is a room. The Hall is a room. "A long hall."
Jumping is an action applying to nothing. Understand "jump" as jumping.
Carry out jumping: move the player to the Hall{}.
'''
    assert "A long hall." in _play_i7(src.format(""), ["jump"]).split(">jump")[1]
    quiet = src.format(", without printing a room description")
    assert "A long hall." not in _play_i7(quiet, ["jump"]).split(">jump")[1]


def test_inventory_annotations_are_editable_responses():
    src = '''"T" by A

The Lab is a room. The lamp is a device in the Lab. The lamp is lit.
{}'''
    assert "a lamp (providing light)" in _play_i7(src.format(""), ["take lamp", "i"])
    edited = src.format('The list writer internal rule response (D) is "lit".\n')
    assert "a lamp (lit)" in _play_i7(edited, ["take lamp", "i"])


def test_a_new_turn_forgets_the_thing_named_last():
    text = _play_i7('''"T" by A

The Lab is a room. Some rocks are in the Lab. "[regarding the rocks][They] [are] here."
Instead of waiting, say "The air [are] still."
''', ["wait"])
    assert "They are here." in text and "The air is still." in text


# ------------------------------------------------------------ activities (ADR-031)
ROOM_OF_THINGS = '''"T" by A

The Lab is a room. "A clean lab."
The lamp is a device in the Lab.
A box is a container in the Lab.
A rock is in the Lab.
The Cellar is below the Lab. The Cellar is dark.
'''


def test_rule_for_printing_the_name_replaces_the_name_everywhere():
    text = _play_i7(ROOM_OF_THINGS + '''
Rule for printing the name of the lamp when the lamp is switched on:
	say "glowing lamp".
''', ["look", "switch on lamp", "take lamp", "i"])
    assert "You can see a lamp, a box and a rock here." in text    # off: the plain name
    assert "You switch the glowing lamp on." in text                 # on: the rule's name
    assert "  a glowing lamp" in text                                 # in the inventory too


def test_a_name_rule_that_names_itself_does_not_loop_forever():
    text = _play_i7(ROOM_OF_THINGS + '''
Rule for printing the name of the box:
	say "[the box] (empty)".
''', ["x box"])
    assert "the box (empty)" in text.lower()


def test_before_and_after_rules_surround_the_name_and_for_rules_are_specific_first():
    text = _play_i7(ROOM_OF_THINGS + '''
Before printing the name of a container:
	say "<".
After printing the name of a container:
	say ">".
Rule for printing the name of something:
	say "thing".
Rule for printing the name of the rock:
	say "pebble".
''', ["look"])
    assert "You can see a thing, a <thing> and a pebble here." in text


def test_continue_the_activity_lets_the_library_name_it():
    text = _play_i7(ROOM_OF_THINGS + '''
Rule for printing the name of the rock:
	say "large ";
	continue the activity.
''', ["look"])
    assert "a large rock" in text


def test_writing_a_paragraph_mentions_the_thing_only_if_it_says_something():
    text = _play_i7(ROOM_OF_THINGS + '''
Rule for writing a paragraph about the rock:
	say "A rock squats in the corner."
Rule for writing a paragraph about the box:
	do nothing.
''', ["look"])
    assert ("A clean lab.\n\nA rock squats in the corner.\n\n"
            "You can see a lamp and a box here.") in text


def test_the_banner_and_the_dark_room_activities():
    text = _play_i7(ROOM_OF_THINGS + '''
After printing the banner text:
	say "(A test.)".
Rule for printing the name of a dark room:
	say "Somewhere Dark".
Rule for printing the description of a dark room:
	say "You see nothing."
''', ["d"])
    assert "I7-lite\n\n(A test.)\n\nLab\n" in text     # the banner, then the after rule
    assert "Somewhere Dark\nYou see nothing." in text


def test_begin_handling_and_end_let_an_authors_rule_run_an_activity():
    swap = ("The quiet body text rule is listed instead of the room description body text rule"
            " in the carry out looking rulebook.\n")
    text = _play_i7(ROOM_OF_THINGS + swap + '''
This is the quiet body text rule:
	if in darkness:
		begin the printing the description of a dark room activity;
		if handling the printing the description of a dark room activity:
			say "Pitch black.";
		end the printing the description of a dark room activity.
''', ["d"])
    assert "Darkness\nPitch black." in text


def test_activity_problems_are_clear():
    for src, message in (
            ("Rule for supplying a missing noun: say \"Eh?\".",
             "'supplying a missing noun' activity"),
            ("Rule for tickling the lamp: say \"Hee.\".", "I know no activity by that name"),
            ("Rule for printing the name: say \"x\".", None),
            ("Rule for printing the name about the lamp: say \"x\".",
             "I expected 'printing the name of <something>'")):
        try:
            compile_i7(ROOM_OF_THINGS + "\n" + src + "\n")
        except I7Problem as e:
            assert message is not None and message in str(e), (src, str(e))
        else:
            assert message is None, src
