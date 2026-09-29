"""Blorb files: zforge finds the Z-code inside (ADR-061)."""
import struct
import subprocess
import sys
from pathlib import Path

import pytest

from zforge.common.blorb import story_bytes
from zforge.common.errors import ZForgeError

ROOT = Path(__file__).resolve().parent.parent


def chunk(kind: bytes, body: bytes) -> bytes:
    return kind + struct.pack(">I", len(body)) + body + (b"\0" if len(body) & 1 else b"")


def blorb(game_kind: bytes, game: bytes, with_index: bool = True) -> bytes:
    """A small Blorb: an optional resource index, a picture, then the game."""
    pict = chunk(b"PNG ", b"not really a picture")
    index_size = 8 + 4 + 12 * 2
    first = 12 + (index_size if with_index else 0)
    body = b""
    if with_index:
        entries = struct.pack(">4sII", b"Pict", 1, first)
        entries += struct.pack(">4sII", b"Exec", 0, first + len(pict))
        body += chunk(b"RIdx", struct.pack(">I", 2) + entries)
    body += pict + chunk(game_kind, game)
    return b"FORM" + struct.pack(">I", 4 + len(body)) + b"IFRS" + body


def test_a_plain_story_is_left_alone():
    assert story_bytes(b"\x08rest of a story") == b"\x08rest of a story"


def test_the_game_is_found_through_the_index():
    game = b"\x08" + bytes(range(40))       # odd length: the pad byte is skipped
    assert story_bytes(blorb(b"ZCOD", game)) == game


def test_without_an_index_the_game_chunk_is_found():
    assert story_bytes(blorb(b"ZCOD", b"\x05zz", with_index=False)) == b"\x05zz"


@pytest.mark.parametrize("data, message", [
    (blorb(b"GLUL", b"glulx"), "Glulx game"),
    (b"FORM" + struct.pack(">I", 4) + b"IFZS", "saved game"),
    (b"FORM" + struct.pack(">I", 4) + b"AIFF", "not a story or a Blorb"),
])
def test_other_files_get_a_clear_message(data, message):
    with pytest.raises(ZForgeError, match=message):
        story_bytes(data, "x.blb")


def test_zforge_runs_a_game_inside_a_blorb(tmp_path):
    story = tmp_path / "hello.z8"
    subprocess.run([sys.executable, "-m", "zforge", "compile", str(ROOT / "examples" / "hello.ni"),
                    "-o", str(story)], cwd=ROOT, check=True, capture_output=True)
    wrapped = tmp_path / "hello.zblorb"
    wrapped.write_bytes(blorb(b"ZCOD", story.read_bytes()))
    script = tmp_path / "moves.txt"
    script.write_text("look\n")
    plain = subprocess.run([sys.executable, "-m", "zforge", "run", str(story), "--script",
                            str(script), "--ui", "plain", "--seed", "1"],
                           cwd=ROOT, capture_output=True, text=True)
    in_blorb = subprocess.run([sys.executable, "-m", "zforge", "run", str(wrapped), "--script",
                               str(script), "--ui", "plain", "--seed", "1"],
                              cwd=ROOT, capture_output=True, text=True)
    assert in_blorb.returncode == 0 and in_blorb.stdout == plain.stdout


@pytest.mark.skipif(not (ROOT / "stories" / "Bronze.zblorb").exists(),
                    reason="fetch with: python -m zbuilder stories")
def test_the_real_bronze_blorb():
    story = story_bytes((ROOT / "stories" / "Bronze.zblorb").read_bytes())
    assert story[0] == 8 and story[0x12:0x18] == b"060503"
