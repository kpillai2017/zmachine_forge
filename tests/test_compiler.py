"""ZIL-lite compiler stages and diagnostics."""
import pytest

from tests.conftest import ROOT, zil
from zforge.compiler.diagnostics import CompileError, Diagnostics
from zforge.compiler.driver import compile_zil
from zforge.compiler.lexer import Kind, Lexer
from zforge.compiler.reader import Form, read


def tokens(src):
    return [(t.kind, t.text) for t in Lexer(src, Diagnostics("t", src)).tokens()]


def test_lexer_kinds():
    assert tokens('<SET X .Y ,Z "hi|there" -5>')[:-1] == [
        (Kind.LANGLE, "<"), (Kind.ATOM, "SET"), (Kind.ATOM, "X"), (Kind.LOCAL, "Y"),
        (Kind.GLOBAL, "Z"), (Kind.STRING, "hi\nthere"), (Kind.NUMBER, "-5"), (Kind.RANGLE, ">")]


def test_reader_skips_semicolon_comments():
    d = Diagnostics("t", "")
    data = read(Lexer(';"comment" <A <B>>', d).tokens(), d)
    assert len(data) == 1 and isinstance(data[0], Form) and isinstance(data[0].items[1], Form)


def test_cond_values_and_else():
    r = zil('<PRINTN <PICK 1>> <PRINTN <PICK 2>> <PRINTN <PICK 3>>',
            "<ROUTINE PICK (N) <COND (<EQUAL? .N 1> 10) (<EQUAL? .N 2> 20) (ELSE 30)>>")
    assert r.transcript.split()[0] == "102030"


def test_repeat_return_and_map_contents():
    r = zil("<PRINTN <COUNT>> <MAP-CONTENTS (O ,BAG) <TELL \" \" D .O>>",
            """<OBJECT BAG> <OBJECT A (IN BAG) (DESC "a")> <OBJECT B (IN BAG) (DESC "b")>
            <ROUTINE COUNT ("AUX" (I 0)) <REPEAT () <SET I <+ .I 1>>
                <COND (<G? .I 4> <RETURN .I>)>>>""")
    assert r.transcript.split() == ["5", "b", "a"] or r.transcript.split() == ["5", "a", "b"]


def test_and_or_short_circuit():
    r = zil('<COND (<OR <ZERO? 1> <SIDE>> <TELL "yes">)> <COND (<AND <ZERO? 1> <SIDE>>) '
            '(ELSE <TELL " no">)>', '<ROUTINE SIDE () <TELL "side "> <RTRUE>>')
    assert " ".join(r.transcript.split()) == "side yes no"


@pytest.mark.parametrize("src,message", [
    ("<ROUTINE GO () <PRINTN .NOPE>>", "unknown local variable .NOPE"),
    ("<GLOBAL G 1> <ROUTINE GO () <PRINTN .G>>", "is a global, use ,G"),
    ("<ROUTINE GO () <FROB 1>>", "unknown routine or form <FROB"),
    ("<ROUTINE GO () <SET 5 1>>", "needs a variable name"),
    ("<ROUTINE MAIN () <RTRUE>>", "every game starts at GO"),
    ("<VERSION 3> <ROUTINE GO () <RTRUE>>", "only <VERSION 5>"),
])
def test_diagnostics(src, message):
    with pytest.raises(CompileError) as err:
        compile_zil(src, "t.zil")
    assert message in str(err.value)


def test_broken_sample_reports_three_errors_with_locations():
    with pytest.raises(CompileError) as err:
        compile_zil((ROOT / "tests/samples/broken.zil").read_text(), "broken.zil")
    text = str(err.value)
    assert all(f"broken.zil:{loc}: error" in text for loc in ("4:13", "5:5", "6:11"))


def test_examples_compile():
    for name in ("hello.zil", "cloak.zil"):
        path = ROOT / "examples" / name
        assert compile_zil(path.read_text(), str(path)).story[:1] == b"\x05"


def test_nested_table_literals_keep_their_own_addresses():
    """<TABLE <LTABLE ...> <LTABLE ...>>: each inner table is its own array
    (they used to share the outer table's name, giving a wrong address)."""
    from zforge.compiler.driver import compile_zil
    from zforge.vm.headless import play
    src = """<VERSION 5>
<GLOBAL RULES <TABLE <LTABLE 11 12> <LTABLE 21>>>
<ROUTINE GO ()
    <TELL N <GET <GET ,RULES 0> 0> " " N <GET <GET ,RULES 0> 2> " "
          N <GET <GET ,RULES 1> 0> " " N <GET <GET ,RULES 1> 1> CR>
    <QUIT>>"""
    story = compile_zil(src, "nested.zil").story
    assert "2 12 1 21" in play(story, []).transcript
