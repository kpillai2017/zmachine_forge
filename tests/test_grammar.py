"""SYNTAX as data (grammar.py), PROG / BIND blocks, VERB? / PRSO? / PRSI?."""
import pytest

from tests.conftest import ROOT, zil
from zforge.compiler import ast
from zforge.compiler.diagnostics import CompileError, Diagnostics
from zforge.compiler.driver import compile_zil, read_source
from zforge.compiler.forms import FormParser
from zforge.compiler.grammar import FIELDS, desugar
from zforge.vm.headless import play


def desugared(src: str):
    d = Diagnostics("t.zil", src)
    program = FormParser(d).parse_program(read_source(src, d))
    desugar(program, d)
    return program, d


def syntax_rows(program):
    table = next(g for g in program.globals if g.name == "SYNTAX-TABLE").init
    count, items = table.items[0].value, table.items[1:]
    size = len(FIELDS)
    assert len(items) == count * size
    return [items[i * size:(i + 1) * size] for i in range(count)]


def show(item):
    if isinstance(item, ast.Word):
        return item.word
    if isinstance(item, ast.Num):
        return item.value
    return item.name


GRAMMAR = """<SYNTAX TAKE OBJECT (FIND TAKEBIT) = V-TAKE>
<SYNTAX PUT OBJECT (HELD CARRIED) (MANY) IN OBJECT (INSIDE-PRSI) = V-PUT-IN PRE-PUT>
<SYNTAX LOOK AROUND = V-LOOK>
<VERB-SYNONYM TAKE GET GRAB>
<PREP-SYNONYM IN INTO>
<ROUTINE V-TAKE () 1> <ROUTINE V-PUT-IN () 1> <ROUTINE PRE-PUT () 1>
<ROUTINE V-LOOK () 1>"""


def test_syntax_becomes_table_rows_with_synonyms():
    program, d = desugared(GRAMMAR)
    assert not d
    rows = [[show(x) for x in row] for row in syntax_rows(program)]
    # verb, nobj, prep1, prep2, find1, find2, opts1, opts2, action#, routine, preaction
    assert rows[0] == ["take", 1, 0, 0, "TAKEBIT", -1, 0, 0, "V?TAKE", "V-TAKE", 0]
    assert [r[0] for r in rows[:3]] == ["take", "get", "grab"]     # VERB-SYNONYM
    assert rows[3] == ["put", 2, 0, "in", -1, -1, 1, 4, "V?PUT-IN", "V-PUT-IN", "PRE-PUT"]
    assert rows[4][3] == "into"                                     # PREP-SYNONYM
    assert rows[5][:4] == ["look", 0, "around", 0]                  # a particle


def test_action_numbers_are_constants_in_first_seen_order():
    program, _ = desugared(GRAMMAR)
    consts = {c.name: c.value.value for c in program.constants}
    assert (consts["V?TAKE"], consts["V?PUT-IN"], consts["V?LOOK"]) == (1, 2, 3)
    assert consts["S-VERB"] == 0 and consts["S-SIZE"] == len(FIELDS) == 11
    assert (consts["SO-HELD"], consts["SO-ROOM"], consts["SO-INSIDE"]) == (1, 2, 4)


@pytest.mark.parametrize("src, message", [
    ("<SYNTAX PUT OBJECT OBJECT OBJECT = V-PUT>", "at most two OBJECTs"),
    ("<SYNTAX DROP OBJECT>", "'= ACTION-ROUTINE'"),
    ("<SYNTAX TAKE OBJECT = V-TAKE> <VERB-SYNONYM FLY SOAR>", "no SYNTAX uses the verb FLY"),
    ("<SYNTAX TAKE OBJECT (NEARBY) = V-TAKE>", "unsupported SYNTAX option"),
    ("<SYNTAX TAKE OBJECT = V-NOPE>", "routine V-NOPE is not defined"),
])
def test_grammar_errors(src, message):
    _, d = desugared(src + " <ROUTINE V-TAKE () 1>")
    assert any(message in item.message for item in d.items), [i.message for i in d.items]


def test_verb_predicates_desugar_to_equal():
    src = "<ROUTINE GO () <VERB? TAKE DROP> <PRSO? LAMP>>"
    d = Diagnostics("t", src)
    body = FormParser(d).parse_program(read_source(src, d)).routines[0].body
    assert body[0].name == "EQUAL?" and [a.name for a in body[0].args] == \
        ["PRSA", "V?TAKE", "V?DROP"]
    assert [a.name for a in body[1].args] == ["PRSO", "LAMP"]


def test_prog_return_again_and_bind_passthrough():
    r = zil('<TELL N <PROG ((X 10)) <COND (<G? .X 5> <RETURN <* .X 2>>)> 99> CR>'
            '<TELL N <PROG ((N 0)) <SET N <+ .N 1>> <COND (<L? .N 4> <AGAIN>)> .N> CR>'
            '<TELL N <BIND ((B 7)) <+ .B 1>> CR>'
            '<TELL N <OUTER> CR>',
            '<ROUTINE OUTER () <PROG () <BIND ((Z 5)) <RETURN <+ .Z 100>>> 0>>')
    assert r.transcript.split() == ["20", "4", "8", "105"]


def test_prog_bindings_are_fresh_each_time():
    r = zil("<SAY> <SAY>", '<ROUTINE SAY () <PROG ((N)) <SET N <+ .N 1>> <PRINTN .N>>>')
    assert r.transcript.strip() == "11"


def test_shadowing_a_variable_is_an_error():
    with pytest.raises(CompileError) as err:
        compile_zil('<VERSION 5> <ROUTINE GO ("AUX" X) <PROG ((X 1)) .X>>', "t.zil")
    assert "shadowing is not supported" in str(err.value)


def test_again_is_not_allowed_in_bind():
    with pytest.raises(CompileError) as err:
        compile_zil("<VERSION 5> <ROUTINE GO () <BIND () <AGAIN>>>", "t.zil")
    assert "AGAIN is only allowed inside PROG" in str(err.value)


def test_parser_library_game_plays():
    path = ROOT / "examples" / "cloak_syntax.zil"
    story = compile_zil(path.read_text(), str(path)).story
    r = play(story, ["pick up the velvet cloak", "w", "hang velvet cloak onto peg", "i"])
    text = r.transcript
    assert "You already have that." in text
    assert "You hang the velvet cloak on the small brass hook." in text
    assert "You are empty-handed." in text


def demo(script):
    path = ROOT / "examples" / "parser_demo.zil"
    return play(compile_zil(path.read_text(), str(path)).story, script).transcript


def test_ambiguous_reply_asks_again_with_fewer_choices():
    text = demo(["take key", "key", "iron", "take book", "the", "red book"])
    assert text.count("Which do you mean, the brass key, the iron key or the rusty key?") == 2
    assert "You take the iron key." in text
    assert text.count("Which do you mean, the red book or the blue book?") == 2
    assert "You take the red book." in text


def test_it_follows_the_last_direct_object():
    text = demo(["take blue book", "x wooden box", "x it", "take brass key", "drop it"])
    assert "A plain wooden box with no lid." in text.split("x it")[1]
    assert "You drop the brass key." in text


def test_empty_reply_cancels_the_question():
    text = demo(["take key", "", "i"])
    assert "I beg your pardon?" in text
    assert "You are empty-handed." in text


def test_zil_search_options_become_preference_bits():
    program, d = desugared("""<ROUTINE V-TAKE () 1>
<SYNTAX TAKE OBJECT (HAVE CARRIED) (TAKE MANY) FROM OBJECT (IN-ROOM) = V-TAKE>
<SYNTAX GET OBJECT (ON-GROUND INSIDE-PRSI) = V-TAKE>""")
    assert not d.items, [i.message for i in d.items]
    rows = [[show(item) for item in row] for row in syntax_rows(program)]
    assert rows[0][6:8] == [1, 2]       # SO-HELD for object 1, SO-ROOM for object 2
    assert rows[1][6:8] == [2 | 4, 0]   # SO-ROOM | SO-INSIDE; TAKE / MANY are ignored


def test_missing_object_is_asked_for_then_both_objects():
    text = demo(["put", "brass key", "box"])
    assert "What do you want to put?" in text
    assert "What do you want to put the brass key in?" in text
    assert "You aren't holding the brass key." in text      # PUT reached the verb

