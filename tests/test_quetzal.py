"""Appendix C Quetzal save files and §15 save_undo/restore_undo."""
from zforge.vm import quetzal
from tests.conftest import zil
from zforge.compiler.driver import compile_zil
from zforge.vm.headless import play

COUNTER = """<VERSION 5> <GLOBAL N 0>
<ROUTINE GO () <SETG N 7> <PRINTN ,N> <QUIT>>"""


def test_compress_decompress_round_trip():
    original = bytes(range(256)) * 4
    current = bytearray(original)
    current[10] ^= 0xFF
    current[900] = 3
    packed = quetzal._compress(bytes(current), original)
    assert quetzal._decompress(packed, original) == current
    assert len(packed) < len(current)


def test_save_file_is_iff_ifzs():
    result = play(compile_zil(COUNTER).story)
    data = quetzal.encode_save(result.vm, result.vm.pc)
    assert data[:4] == b"FORM" and data[8:12] == b"IFZS"
    assert b"IFhd" in data and b"CMem" in data and b"Stks" in data


def test_undo_restores_state():
    r = zil("<SETG N 1> <COND (<EQUAL? <ZOP SAVE_UNDO> 2> <TELL \"back \"> <PRINTN ,N> <QUIT>)>"
            "<SETG N 99> <ZOP RESTORE_UNDO>", "<GLOBAL N 0>")
    assert " ".join(r.transcript.split()) == "back 1"
