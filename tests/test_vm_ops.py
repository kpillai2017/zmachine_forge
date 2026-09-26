"""Opcode behaviour, driven through tiny compiled programs."""
import pytest

from tests.conftest import story, zas, zil


def lines(result):
    return [ln for ln in result.transcript.splitlines() if ln.strip()]


def test_arithmetic_semantics():
    r = zil('<PRINTN </ -7 2>> <TELL " "> <PRINTN <MOD -7 2>> <TELL " "> '
            '<PRINTN <+ 32767 1>> <TELL " "> <PRINTN <* -3 4>>')
    assert lines(r) == ["-3 -1 -32768 -12"]


def test_division_by_zero_is_a_clear_error():
    r = zas(".main GO\n.routine GO\n    div 1 0 -> sp\n    quit\n.end\n")
    assert not r.ok and "Division by zero" in r.reason


def test_indirect_variable_on_stack_top_in_place():
    # §6.3.4: `inc sp` modifies the top of stack in place - no push/pop
    r = zas(".main GO\n.routine GO\n    push 41\n    inc sp\n    print_num sp\n    quit\n.end\n")
    assert lines(r) == ["42"]


def test_calls_locals_and_return_values():
    r = zil("<PRINTN <ADD3 1 2 3>>", "<ROUTINE ADD3 (A B C) <+ .A .B .C>>")
    assert lines(r) == ["6"]


def test_optional_args_use_check_arg_count():
    r = zil('<PRINTN <F>> <TELL " "> <PRINTN <F 5>>', '<ROUTINE F ("OPT" (X 9)) .X>')
    assert lines(r) == ["9 5"]


def test_catch_and_throw():
    r = zas(""".main GO
.routine GO
    call_1s OUTER -> sp
    print_num sp
    quit
.end
.routine OUTER .frame
    catch -> .frame
    call_2n INNER .frame
    ret 1
.end
.routine INNER .frame
    throw 77 .frame
.end
""")
    assert lines(r) == ["77"]


def test_random_is_seeded_and_in_range():
    r = zil("<DO (I 1 20) <PRINTN <RANDOM 6>>>")
    digits = lines(r)[0]
    assert len(digits) == 20 and set(digits) <= set("123456")


def test_output_stream_3_captures_text_to_memory():
    r = zil("<ZOP OUTPUT_STREAM 3 ,BUF> <TELL \"abc\"> <ZOP OUTPUT_STREAM -3> "
            "<PRINTN <GET ,BUF 0>> <TELL \" \"> <PRINTC <GETB ,BUF 2>>",
            "<GLOBAL BUF <ITABLE 20 (BYTE)>>")
    assert lines(r) == ["3 a"]


def test_czech_passes():
    r = __import__("zforge.vm.headless", fromlist=["play"]).play(story("czech.z5"))
    assert "Failed: 0" in r.transcript


@pytest.mark.parametrize("name,script,expect", [("praxix.z5", ["all"], "All tests passed")])
def test_praxix_passes(name, script, expect):
    from zforge.vm.headless import play
    assert expect in play(story(name), script).transcript
