"""§12 object tree and properties, §13 dictionary and tokenising."""
from tests.conftest import zil

OBJECTS = """
<OBJECT BOX (DESC "box") (SIZE 5) (NAMES 1 2 3) (FLAGS OPENBIT)>
<OBJECT BALL (IN BOX) (DESC "ball") (SYNONYM BALL SPHERE)>
<OBJECT CUBE (IN BOX) (DESC "cube")>
"""


def out(r):
    return " ".join(r.transcript.split())


def test_tree_move_and_remove():
    r = zil("<TELL D <FIRST? ,BOX> \" \"> <REMOVE ,BALL> <TELL D <FIRST? ,BOX> \" \">"
            "<MOVE ,BALL ,CUBE> <TELL D <LOC ,BALL>>", OBJECTS)
    assert out(r) == "ball cube cube"


def test_attributes_and_properties():
    r = zil("<COND (<FSET? ,BOX ,OPENBIT> <TELL \"open \">)> <FCLEAR ,BOX ,OPENBIT>"
            "<COND (<NOT <FSET? ,BOX ,OPENBIT>> <TELL \"shut \">)>"
            "<PRINTN <GETP ,BOX ,P?SIZE>> <TELL \" \"> <PUTP ,BOX ,P?SIZE 9>"
            "<PRINTN <GETP ,BOX ,P?SIZE>> <TELL \" \"> <PRINTN <PTSIZE <GETPT ,BOX ,P?NAMES>>>"
            "<TELL \" \"> <PRINTN <GETP ,BALL ,P?SIZE>>", OBJECTS)
    assert out(r) == "open shut 5 9 6 0"          # a missing property reads its default


def test_tokenise_finds_dictionary_words():
    r = zil("<PUTB ,TB 0 40> <PUTB ,PB 0 4> <READ ,TB ,PB>"
            "<PRINTN <GETB ,PB 1>> <TELL \" \">"
            "<COND (<EQUAL? <GET ,PB 1> ,W?SPHERE> <TELL \"sphere \">)>"
            "<COND (<ZERO? <GET ,PB 3>> <TELL \"unknown\">)>",
            OBJECTS + "<GLOBAL TB <ITABLE 42 (BYTE)>> <GLOBAL PB <ITABLE 20 (BYTE)>>",
            script=["Sphere xyzzy"])
    assert out(r).endswith("2 sphere unknown")
