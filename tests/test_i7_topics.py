"""Topics: Inform 7's [text] token, the topic understood, topic patterns, and
the four actions on a topic (docs/TOPICS_PLAN.md, steps A and B).

The default replies were checked against Cold Iron, built with the official
Inform 7: LOOK UP / CONSULT, ASK, TELL (yourself) and ANSWER give the same
words there as here."""

from __future__ import annotations

import pytest

from zforge.compiler.i7.driver import compile_i7
from zforge.compiler.i7.problems import I7Problem
from zforge.vm.headless import play

STORY = '''"Topics" by Test

The Study is a room. The notes are in the Study. The notes are plural-named.
The Beast is a man in the Study.
'''


def replies(source: str, commands: list[str]) -> list[str]:
    """The reply to each command, in order."""
    out = play(compile_i7(STORY + source, "topics.ni", 8).story, commands).transcript
    return [chunk.partition("\n")[2].strip() for chunk in out.split("\n>")[1:]][:len(commands)]


# ------------------------------------------------ step A: the [text] token
PONDER = ('Pondering is an action applying to one topic. '
          'Understand "ponder [text]" as pondering.\n'
          'Carry out pondering: say "You ponder [the topic understood]."\n'
          'Searching it for is an action applying to one thing and one topic.\n'
          'Understand "search [something] for [text]" and "hunt [text] in [something]" '
          'as searching it for.\n'
          'Carry out searching something for: say "[The noun]: [the topic understood]."\n')


def test_a_topic_is_the_words_typed_even_unknown_ones():
    got = replies(PONDER, ["ponder the rose garden", "ponder zanzibar and xyzzy"])
    assert got[0] == "You ponder the rose garden."
    assert got[1] == "You ponder zanzibar and xyzzy."


def test_the_thing_is_the_noun_whichever_slot_it_is_typed_in():
    got = replies(PONDER, ["search notes for elephant", "hunt djinn in notes"])
    assert got == ["The notes: elephant.", "The notes: djinn."]


def test_unknown_words_outside_a_topic_are_still_errors():
    got = replies(PONDER, ["x zanzibar", "hunt djinn in qwerty", "xyzzy"])
    assert got == ["You can't see any such thing.", "You can't see any such thing.",
                   "That's not a verb I recognise."]


def test_a_missing_topic_is_not_understood_as_in_inform():
    # Cold Iron: CONSULT ME / TELL ME -> "I didn't understand that sentence."
    assert replies(PONDER, ["ponder"]) == ["I didn't understand that sentence."]


def test_text_is_only_for_actions_on_a_topic():
    with pytest.raises(I7Problem, match="does not apply to a topic"):
        compile_i7(STORY + 'Understand "sniff [text]" as examining.', "t.ni", 8)


# ------------------------------------------------ step B: patterns and actions
RULES = ('Instead of consulting the notes about "roses/rose/garden" or "rose garden", '
         'say "Roses."\n'
         'Instead of consulting the notes about "the/-- djinn", say "Djinn."\n'
         'Instead of asking the Beast about "himself", say "He growls."\n'
         'Instead of asking the Beast about when the topic understood includes "father", '
         'say "He looks away."\n'
         'Instead of answering the Beast that "yes", say "He nods."\n')


def test_slashes_separate_words_and_or_separates_phrases():
    # "roses/rose/garden" is one word, any of the three; "rose garden" is two.
    got = replies(RULES, ["look up roses in notes", "look up rose garden in notes",
                          "look up garden in notes", "look up roses garden in notes"])
    assert got == ["Roses.", "Roses.", "Roses.",
                   "You discover nothing of interest in the notes."]


def test_a_rule_topic_must_match_all_the_words():
    got = replies(RULES, ["look up the rose garden in notes", "look up rose in notes"])
    assert got == ["You discover nothing of interest in the notes.", "Roses."]


def test_a_word_marked_with_dashes_may_be_left_out():
    assert replies(RULES, ["look up the djinn in notes", "look up djinn in notes"]) == \
        ["Djinn.", "Djinn."]


def test_includes_finds_a_word_anywhere_in_the_topic():
    got = replies(RULES, ["ask beast about my father", "ask beast about fathers"])
    assert got == ["He looks away.", "There is no reply."]


def test_the_default_replies_are_informs():
    got = replies("", ["look up xyzzy in me", "consult notes about plugh",
                       "read about elephant in notes", "ask beast about the cave",
                       "tell beast about the cave", "tell me about the cave",
                       "answer yes to beast", "say no to beast"])
    assert got == ["You discover nothing of interest in yourself.",
                   "You discover nothing of interest in the notes.",
                   "You discover nothing of interest in the notes.",
                   "There is no reply.", "This provokes no reaction.",
                   "You talk to yourself a while.",
                   "There is no reply.", "There is no reply."]


def test_rules_beat_the_default_replies():
    assert replies(RULES, ["ask beast about himself", "say yes to beast"]) == \
        ["He growls.", "He nods."]


def test_a_topic_condition_can_be_negated():
    source = ('Instead of telling the Beast about:\n'
              '\tif the topic understood does not include "roses", continue the action;\n'
              '\tsay "He smiles at [the topic understood]."\n')
    got = replies(source, ["tell beast about the roses outside", "tell beast about lilies"])
    assert got == ["He smiles at the roses outside.", "This provokes no reaction."]


def test_a_topic_must_be_in_quotation_marks():
    with pytest.raises(I7Problem, match="quotation marks"):
        compile_i7(STORY + "Instead of asking the Beast about roses, say \"No.\"", "t.ni", 8)


# ------------------------------------------------ step C: topic tables
TABLES = ('Instead of consulting the notes about a topic listed in the Table of Notes:\n'
          '\tsay "[reply entry]".\n'
          'Instead of asking the Beast about a topic listed in the Table of Talk:\n'
          '\tsay "[The Beast] says, [answer entry]"\n'
          'Pondering is an action applying to one topic. Understand "ponder [text]" as pondering.\n'
          'Carry out pondering:\n'
          '\tif the topic understood is a topic listed in the Table of Notes:\n'
          '\t\tsay "You recall: [reply entry]";\n'
          '\totherwise:\n'
          '\t\tsay "Nothing about [the topic understood]."\n'
          '\n'
          'Table of Notes\n'
          'topic\treply\n'
          '"rose/roses/garden" or "rose garden"\t"Roses of her own breeding."\n'
          '"the/-- djinn"\t"A djinn, [italic type]bound[roman type] in brass."\n'
          '\n'
          'Table of Talk\n'
          'topic\tanswer\n'
          '"roses"\t"they were hers."\n')


def test_a_topic_listed_in_a_table_finds_its_row():
    got = replies(TABLES, ["look up rose garden in notes", "look up the djinn in notes",
                           "look up zanzibar in notes"])
    assert got == ["Roses of her own breeding.", "A djinn, bound in brass.",
                   "You discover nothing of interest in the notes."]


def test_each_table_has_its_own_columns():
    assert replies(TABLES, ["ask beast about roses"]) == ["The Beast says, they were hers."]


def test_a_table_can_be_looked_up_in_a_condition():
    assert replies(TABLES, ["ponder roses", "ponder zanzibar"]) == \
        ["You recall: Roses of her own breeding.", "Nothing about zanzibar."]


def test_a_table_needs_one_topic_column():
    with pytest.raises(I7Problem, match="topic"):
        compile_i7(STORY + '\nTable of Scores\nname\tvalue\n"a"\t"b"\n', "t.ni", 8)


def test_a_rule_must_name_a_table_that_exists():
    with pytest.raises(I7Problem, match="no table called"):
        compile_i7(STORY + 'Instead of consulting the notes about a topic listed in the '
                   'Table of Nothing:\n\tsay "x".', "t.ni", 8)


# ------------------------------------------- quoted text over several lines
def test_a_blank_line_inside_a_quote_is_a_paragraph_break():
    from zforge.compiler.i7.source import join_quoted_lines
    lines, origin = join_quoted_lines(['The Hall is a room. "One', 'two.', '', 'Three."', 'X.'])
    assert lines == ['The Hall is a room. "One two.[paragraph break]Three."', 'X.']
    assert origin == [1, 5]


def test_an_unclosed_quote_is_left_alone():
    from zforge.compiler.i7.source import join_quoted_lines
    lines, origin = join_quoted_lines(['The Hall is a room. "Oops.', 'X.'])
    assert lines == ['The Hall is a room. "Oops.', 'X.'] and origin == [1, 2]


def test_problems_after_a_long_quote_name_the_right_line():
    source = STORY + 'The Hall is a room. "One.\n\nTwo."\n\nThe notes are xyzzy.\n'
    line = STORY.count("\n") + 5
    with pytest.raises(I7Problem, match=f"t.ni:{line}:"):
        compile_i7(source, "t.ni", 8)


def test_a_table_entry_may_go_on_over_several_lines():
    source = (STORY
              + 'Instead of consulting the notes about a topic listed in the Table of Notes:\n'
              '\tsay "[reply entry][paragraph break]".\n\n'
              'Table of Notes\ntopic\treply\n'
              '"djinn"\t"A djinn.\n\nBound in brass."\n'
              '"roses"\t"Roses."\n')
    assert replies(source, ["look up djinn in notes", "look up roses in notes"]) == \
        ["A djinn.\n\nBound in brass.", "Roses."]


# ------------------------------------------------------ found in step D
def test_a_rule_may_leave_out_the_topic():
    source = 'Instead of consulting the notes, say "The notes are in code."'
    assert replies(source, ["look up djinn in notes"]) == ["The notes are in code."]


def test_a_story_may_have_more_topics_than_globals():
    # letters only: a digit takes two of a dictionary word's nine letter-codes
    names = [f"w{a}{b}" for a in "abcdefghijklmnopqrstuvwxyz" for b in "abcdefghijklm"][:300]
    rows = "".join(f'"{name}"\t"Entry {name}."\n' for name in names)
    source = ('Instead of consulting the notes about a topic listed in the Table of Words:\n'
              '\tsay "[reply entry]".\n\nTable of Words\ntopic\treply\n' + rows)
    assert replies(source, ["look up wwf in notes"]) == ["Entry wwf."]


PARAGRAPHS = ('Humming is an action applying to nothing. Understand "hum" as humming.\n'
              'Instead of humming, say "Up.[paragraph break]".\n'
              'Instead of waiting:\n\tsay "One.[paragraph break]";\n\tsay "Two."\n')


def test_a_paragraph_break_at_the_end_owes_no_extra_line_before_the_prompt():
    out = play(compile_i7(STORY + PARAGRAPHS, "t.ni", 8).story, ["hum"]).transcript
    assert "Up.\n\n>" in out and "Up.\n\n\n>" not in out


def test_a_paragraph_break_still_divides_what_follows():
    assert replies(PARAGRAPHS, ["wait"]) == ["One.\n\nTwo."]


# ------------------------------------------------- (with nouns reversed)
REVERSED_STORY = ('A post is in the Study. The player carries a rope.\n'
                  'Tying it to is an action applying to two things.\n'
                  'Understand "tie [something] to [something]" as tying it to.\n'
                  'Understand "fasten [something] with [something]" as tying it to '
                  '(with nouns reversed).\n'
                  'Carry out tying something to something: '
                  'say "You tie [the noun] to [the second noun]."\n')


def test_nouns_reversed_swaps_the_two_things():
    assert replies(REVERSED_STORY, ["tie rope to post", "fasten post with rope"]) == \
        ["You tie the rope to the post.", "You tie the rope to the post."]


def test_a_topic_line_may_say_with_nouns_reversed():
    source = ('Understand "research [text] in [something]" as consulting it about '
              '(with nouns reversed).\n'
              'Instead of consulting the notes about "djinn", say "A djinn."\n')
    assert replies(source, ["research djinn in notes"]) == ["A djinn."]


def test_only_two_noun_actions_can_be_reversed():
    with pytest.raises(I7Problem, match="cannot be reversed"):
        compile_i7(STORY + 'Understand "peer at [something]" as examining '
                   '(with nouns reversed).\n', "t.ni", 8)
