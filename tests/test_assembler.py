"""Assembler: forms, branch relaxation, header and checksum."""
import pytest

from tests.conftest import ROOT, zas
from zforge.asm.assembler import assemble
from zforge.asm.disasm import disassemble
from zforge.asm.syntax import AsmError
from zforge.common.header import Header, compute_checksum


def test_hello_zas_assembles_and_runs():
    r = zas((ROOT / "tests" / "samples" / "hello.zas").read_text())
    assert "Hello, world!" in r.transcript


def test_header_is_valid_and_checksum_matches():
    story = assemble(".main GO\n.routine GO\n    quit\n.end\n")
    h = Header.parse(story)
    assert h.version == 5 and h.file_length == len(story)
    assert compute_checksum(story, len(story)) == h.checksum
    assert h.high_memory % 4 == 0 and h.static_memory <= h.high_memory


def test_long_branch_is_relaxed():
    far = "\n".join(["    print \"padding padding padding\""] * 20)
    text = f".main GO\n.routine GO\n    jz 0 ?far\n{far}\nfar:\n    print \"ok\"\n    quit\n.end\n"
    story = assemble(text)
    assert "ok" in zas(text).transcript
    assert "jz" in disassemble(story)


def test_unknown_label_and_opcode_are_errors():
    with pytest.raises(AsmError):
        assemble(".main GO\n.routine GO\n    jump nowhere\n.end\n")
    with pytest.raises(AsmError):
        assemble(".main GO\n.routine GO\n    frobnicate 1\n.end\n")
