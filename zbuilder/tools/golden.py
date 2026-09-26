"""Tool 10: golden - freeze what the toolchain produces TODAY, so a
refactor can prove it changed nothing (proforma v2, eval case
refactor-byte-identical).

    python -m zbuilder golden --record   # a HUMAN runs this once, before Tier 5
    python -m zbuilder golden --check    # every tier gate runs this

For every golden source we store the sha256 of
  * the story file bytes,
  * the disassembly text (zforge disasm), and
  * the header report (zforge info --header).
The story file is the real contract; the two text hashes make a failure
easier to understand ("the bytes changed AND the code changed" versus "only
the header changed").

Agents never write tests/golden/: files.py refuses that path. Re-recording
needs a human and an ADR.
"""
from __future__ import annotations

import hashlib
import json

from zbuilder.paths import PROJECT_ROOT

GOLDEN_DIR = PROJECT_ROOT / "tests" / "golden"
GOLDEN_FILE = GOLDEN_DIR / "v1_hashes.json"

# Sources whose output is frozen. The .zil files that are MEANT to fail
# (broken*.zil) are not here; the compile-error eval cases cover them.
ASM_SOURCES = ["tests/samples/hello.zas"]
ZIL_SOURCES = ["examples/hello.zil", "examples/cloak.zil", "examples/cloak_syntax.zil",
               "examples/parser_demo.zil", "tests/samples/arith.zil", "tests/samples/prog.zil"]


def _sha(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def build_story(source: str) -> bytes:
    """Build one golden source with the CURRENT defaults (target z5)."""
    path = PROJECT_ROOT / source
    if source.endswith(".zas"):
        from zforge.asm.assembler import assemble
        return assemble(path.read_text(), str(path))
    from zforge.compiler.driver import compile_zil
    return compile_zil(path.read_text(), str(path)).story


def fingerprint(source: str) -> dict:
    from zforge.asm.disasm import disassemble
    from zforge.asm.info import header_report
    story = build_story(source)
    return {"size": len(story), "story": _sha(story),
            "disasm": _sha(disassemble(story)), "header": _sha(header_report(story))}


def current() -> dict[str, dict]:
    return {src: fingerprint(src) for src in ASM_SOURCES + ZIL_SOURCES}


def record() -> list[str]:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    data = current()
    GOLDEN_FILE.write_text(json.dumps({"about": "zforge v1 outputs (target z5), "
                                       "recorded before the Tier 5 refactor",
                                       "sources": data}, indent=1) + "\n")
    return [f"recorded {src} ({fp['size']} bytes)" for src, fp in data.items()]


def check() -> list[str]:
    """Return a list of problems; empty means byte-identical."""
    if not GOLDEN_FILE.exists():
        return [f"{GOLDEN_FILE.relative_to(PROJECT_ROOT)} missing: "
                "run `python -m zbuilder golden --record` once"]
    want = json.loads(GOLDEN_FILE.read_text())["sources"]
    problems = []
    for src, expected in want.items():
        got = fingerprint(src)
        changed = [k for k in ("story", "disasm", "header") if got[k] != expected[k]]
        if got["size"] != expected["size"]:
            changed.append(f"size {expected['size']} -> {got['size']}")
        if changed:
            problems.append(f"{src}: changed {', '.join(changed)}")
    return problems
