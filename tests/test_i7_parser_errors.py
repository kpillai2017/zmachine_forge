"""Parser errors, rule placement, phrases with parameters and their friends.

Each test compiles a small I7-lite story, plays it and reads what the
player would see. The exact wording of Inform 7's messages was checked
against the real Advent_Crowther.z8 where that game can show it (ADR-034).
"""
import pytest

from zforge.compiler.driver import compile_zil
from zforge.compiler.diagnostics import CompileError
from zforge.compiler.i7.driver import compile_i7
from zforge.compiler.i7.problems import I7Problem
from zforge.vm.headless import play

HEAD = '"Test" by Tester\n\nThe Lab is a room. A brass lamp is in the Lab.\n\n'


def run(body: str, commands: list[str]) -> str:
    story = compile_i7(HEAD + body, "test.ni", target=8).story
    t = play(story, commands).transcript
    return t[t.index(">"):]


def problems_of(body: str) -> str:
    with pytest.raises(I7Problem) as e:
        compile_i7(HEAD + body, "test.ni", target=8)
    return str(e.value)


# ------------------------------------------------ ZIL-lite compilation flags
ZIL_HEAD = '<VERSION 5>\n<ROUTINE GO () <SAY> <QUIT>>\n'


def zil_output(src: str) -> str:
    story = compile_zil(ZIL_HEAD + src, "t.zil", 5).story
    return play(story, []).transcript


def test_ifflag_chooses_the_clause_of_the_first_true_flag():
    src = ('<COMPILATION-FLAG FANCY T>\n'
           '<ROUTINE SAY () <IFFLAG (FANCY <PRINTI "fancy"> <PRINTI "!">) (ELSE <PRINTI "plain">)>'
           ' <CRLF>>')
    assert zil_output(src).startswith("fancy!")


def test_ifflag_else_and_the_default_flag():
    src = ('<COMPILATION-FLAG-DEFAULT FANCY <>>\n'
           '<ROUTINE SAY () <IFFLAG (FANCY <PRINTI "fancy">) (ELSE <PRINTI "plain">)> <CRLF>>')
    assert zil_output(src).startswith("plain")
    # a default does not change a flag that is already set
    src = '<COMPILATION-FLAG FANCY T>\n' + src
    assert zil_output(src).startswith("fancy")


def test_ifflag_with_an_unknown_flag_is_an_error():
    with pytest.raises(CompileError) as e:
        compile_zil(ZIL_HEAD + '<ROUTINE SAY () <IFFLAG (FANCEY <PRINTI "x">) (ELSE)>>',
                    "t.zil", 5)
    assert "no compilation flag FANCEY" in str(e.value)


# ------------------------------------------------------------ parser errors
@pytest.mark.parametrize("command, message", [
    ("", "I beg your pardon?"),
    ("frobnicate", "That's not a verb I recognise."),
    ("take zorkmid", "You can't see any such thing."),
    ("x it", "I'm not sure what 'it' refers to."),        # single quotes: the real game's
])
def test_each_parser_error_has_inform_7s_message(command, message):
    assert message in run("", [command])


def test_it_gone_names_the_word_and_the_thing():
    out = run("The Hall is east of the Lab.", ["x lamp", "e", "x it"])
    assert "You can't see 'it' (the brass lamp) at the moment." in out


def test_a_rule_can_replace_one_error_and_an_after_rule_adds_to_all():
    out = run('Rule for printing a parser error when the latest parser error is the '
              'not a verb I recognise error:\n\tsay "I don\'t know that word."\n\n'
              'After printing a parser error: say "(Oops.)"\n', ["frobnicate", "take zorkmid"])
    assert "I don't know that word.\n(Oops.)" in out         # a message, not a paragraph
    assert "You can't see any such thing.\n(Oops.)" in out


def test_an_error_the_parser_never_makes_is_never_the_latest():
    # before any error, the latest parser error must not look like one of these
    out = run('Every turn when the latest parser error is the nothing to do error:\n'
              '\tsay "Wrong!"\n', ["wait", "frobnicate", "wait"])
    assert "Wrong!" not in out


# ------------------------------------------------------------ first / last
def test_first_puts_a_rule_before_more_specific_ones():
    out = run('The count is a number that varies.\n'
              'After printing a parser error when the count is 1: say "(one)"\n'
              'The first after printing a parser error rule: increment the count.\n',
              ["frobnicate"])
    assert "(one)" in out


def test_first_and_last_in_action_and_every_turn_rulebooks():
    out = run('Last every turn: say "C".\nEvery turn: say "B".\nFirst every turn: say "A".\n'
              'Last instead of taking the lamp: say "late".\n'
              'Instead of taking the lamp: say "early".\n', ["wait", "take lamp"])
    assert out.index("A") < out.index("B") < out.index("C")
    assert "early" in out and "late" not in out


# ---------------------------------------------- phrases with parameters
def test_phrases_take_texts_numbers_and_things():
    out = run('The count is a number that varies.\n'
              'To praise (item - a thing) times (n - a number):\n'
              '\tsay "What a fine [item]!";\n\tincrease the count by n.\n'
              'To say fancy (item - a thing): say "*[the item]*".\n'
              'To decide whether (item - a thing) is gleaming:\n'
              '\tif the item is the brass lamp, decide yes;\n\tdecide no.\n'
              'To announce (message - a text): say "[message] [message]".\n'
              'To echo (message - a text): announce message.\n'
              'Instead of waiting:\n\tpraise the brass lamp times 3;\n'
              '\tsay "[count] [fancy brass lamp].";\n'
              '\tif the brass lamp is gleaming, say "Gleams.";\n'
              '\techo "Hi[if the count is 3]![end if]".\n', ["wait"])
    assert "What a fine brass lamp!" in out and "3 *the brass lamp*." in out
    assert "Gleams." in out and "Hi! Hi!" in out


def test_a_preamble_can_go_on_in_lines_that_start_with_a_space():
    out = run('To pose (q - a text)\n with answer (a - a text):\n\tsay "[q] [a]".\n'
              'Instead of waiting,\n pose "Why?" with answer "Because.".\n', ["wait"])
    assert "Why? Because." in out


def test_a_text_that_uses_a_phrases_own_names_is_refused_clearly():
    msg = problems_of('To echo (message - a text): say message.\n'
                      'To shout (message - a text): echo "[message]!".\n')
    assert "a name that only exists inside this rule or phrase" in msg


def test_a_parameter_of_an_unknown_kind_is_refused_clearly():
    assert "a parameter of kind 'colour'" in problems_of('To paint (c - a colour): say "x".\n')


# ------------------------------------- let, repeat, while, increment, decide
def test_let_repeat_and_while():
    out = run('The count is a number that varies.\nInstead of waiting:\n'
              '\tlet x be 3;\n\trepeat with i running from 1 to x:\n\t\tincrease the count by i;\n'
              '\twhile the count is less than 10:\n\t\tincrement the count;\n'
              '\tlet x be 7;\n\tlet the reply be "Done";\n'
              '\tsay "[reply]: [count], [x].".\n', ["wait"])
    assert "Done: 10, 7." in out


def test_decrement():
    out = run('The count is a number that varies.\nWhen play begins: now the count is 5.\n'
              'Instead of waiting: decrement the count; say "[count]".\n', ["wait"])
    assert "4" in out


# ---------------------------------------------------- smaller conveniences
def test_a_description_as_the_subject_of_a_condition():
    out = run('A box is a container in the Lab. The box is openable and closed.\n'
              'Instead of waiting when the closed box is in the location: say "Shut."\n'
              'Instead of taking the lamp when the open box is in the location: say "Open!"\n',
              ["wait", "take lamp"])
    assert "Shut." in out and "Open!" not in out


def test_regarding_them_and_brackets():
    out = run('Instead of waiting:\n'
              '\tsay "[bracket]There [regarding them][are] two.[close bracket]".\n',
              ["wait"])
    assert "[There are two.]" in out
