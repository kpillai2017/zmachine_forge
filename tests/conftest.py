"""Shared fixtures: compile a ZIL snippet or assemble .zas and play it."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from zforge.asm.assembler import assemble  # noqa: E402
from zforge.compiler.driver import compile_zil  # noqa: E402
from zforge.vm.headless import play  # noqa: E402


def zil(body: str, routines: str = "", script=None):
    """Compile `<ROUTINE GO () body <QUIT>>` (+ extra routines) and play it."""
    source = f"<VERSION 5>\n{routines}\n<ROUTINE GO () {body} <QUIT>>\n"
    return play(compile_zil(source, "test.zil").story, script or [])


def zas(text: str, script=None):
    return play(assemble(text, "test.zas"), script or [])


def story(name: str) -> bytes:
    path = ROOT / "stories" / name
    if not path.exists():
        pytest.skip(f"{name} not downloaded (python -m zbuilder stories)")
    return path.read_bytes()
