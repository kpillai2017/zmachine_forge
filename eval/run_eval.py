"""The eval harness: runs every case in eval/cases.json and prints one
PASS / FAIL / SKIP line each. Exit status 1 if anything FAILED.

    python -m eval.run_eval            # all cases
    python -m eval.run_eval undo czech # only cases whose id contains a word

Story-file cases SKIP (not fail) when the story isn't downloaded yet:
run `python -m zbuilder stories` first.
"""
from __future__ import annotations

import inspect
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from zforge.common.errors import ZForgeError  # noqa: E402
from zforge.compiler.driver import compile_zil  # noqa: E402
from zforge.vm.headless import play  # noqa: E402


class Skip(Exception):
    pass


def _compile(path: str) -> bytes:
    src = ROOT / path            # absolute, so INSERT-FILE resolves from any cwd
    return compile_zil(src.read_text(), str(src)).story


def _check_text(case: dict, text: str) -> list[str]:
    problems = [f"missing {s!r}" for s in case.get("must_contain", []) if s not in text]
    problems += [f"unexpected {s!r}" for s in case.get("must_not_contain", []) if s in text]
    if "must_contain_lines" in case:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        want = case["must_contain_lines"]
        if lines[:len(want)] != want:
            problems.append(f"lines were {lines[:len(want)]}, expected {want}")
    return problems


def run_story_case(case: dict) -> list[str]:
    path = ROOT / case["story"]
    if not path.exists():
        raise Skip(f"{case['story']} not downloaded (python -m zbuilder stories)")
    result = play(path.read_bytes(), case.get("script", []))
    return _check_text(case, result.transcript + "\n" + result.reason)


def run_compile_run(case: dict) -> list[str]:
    result = play(_compile(case["source"]), case.get("script", []))
    return _check_text(case, result.transcript + "\n" + result.reason)


def run_screen(case: dict) -> list[str]:
    result = play(_compile(case["source"]), case.get("script", []))
    rows = result.screen.rows
    row0 = "".join(c.char for c in rows[0])
    problems = [f"status row lacks {s!r}: {row0!r}" for s in case["row0_contains"] if s not in row0]
    if case.get("row0_reverse") and not all(c.style & 1 for c in rows[0]):
        problems.append("status row is not entirely reverse video")
    return problems


def run_save_restore(case: dict) -> list[str]:
    """Real §15 save/restore opcodes through the game's SAVE/RESTORE verbs."""
    story = _compile(case["source"])
    with tempfile.TemporaryDirectory() as tmp:
        save_file = str(Path(tmp) / "game.qzl")
        script = [line.replace("{save_file}", save_file) for line in case["script"]]
        result = play(story, script)
        problems = _check_text(case, result.transcript)
        if not Path(save_file).exists():
            problems.append("no save file was written")
        elif Path(save_file).read_bytes()[8:12] != b"IFZS":
            problems.append("save file is not a Quetzal FORM IFZS")
        return problems


def run_compile_error(case: dict) -> list[str]:
    src = ROOT / case["source"]
    try:
        compile_zil(src.read_text(), case["source"])
    except ZForgeError as exc:
        text = str(exc)
        problems = [f"no diagnostic at {loc}" for loc in case["expect_errors"]
                    if f":{loc}: error:" not in text]
        if "Traceback" in text:
            problems.append("a Python traceback leaked into the diagnostics")
        return problems
    return ["compiled without errors"]


def run_reject(case: dict) -> list[str]:
    from zforge.vm.machine import ZMachine
    from zforge.vm.screen.virtual import VirtualScreen
    story = bytearray(_compile("examples/hello.zil"))
    story[0] = 3
    try:
        ZMachine(bytes(story), VirtualScreen())
    except ZForgeError as exc:
        return [] if case["expect"] in str(exc) else [f"message was {exc}"]
    return ["a version-3 file was accepted"]


def run_reject_truncated(case: dict) -> list[str]:
    from zforge.vm.machine import ZMachine
    from zforge.vm.screen.virtual import VirtualScreen
    try:
        ZMachine(_compile("examples/hello.zil")[:20], VirtualScreen())
    except ZForgeError as exc:
        return [] if case["expect"] in str(exc) else [f"message was {exc}"]
    return ["a truncated file was accepted"]


def run_disasm(case: dict) -> list[str]:
    from zforge.asm.disasm import disassemble
    return _check_text(case, disassemble(_compile(case["source"])))


def run_audit(case: dict) -> list[str]:
    from zforge.vm.ops import HANDLERS
    return [f"{name}: handler {fn.__name__} has no § citation"
            for name, fn in HANDLERS.items() if "§" not in (inspect.getdoc(fn) or "")]


def run_spec_opcodes(case: dict) -> list[str]:
    from zforge.common.opcodes import OPCODES
    path = ROOT / "spec" / "opcodes.json"
    if not path.exists():
        raise Skip("spec/opcodes.json missing (python -m zbuilder spec)")
    spec = {(o["kind"], o["number"]): o for o in json.loads(path.read_text())["opcodes"]}
    problems = [] if len(spec) == 98 else [f"spec lists {len(spec)} v5 opcodes, expected 98"]
    ours = {(o.kind, o.number): o for o in OPCODES}
    for key in spec.keys() | ours.keys():
        a, b = spec.get(key), ours.get(key)
        if a is None or b is None:
            problems.append(f"{key} only in {'ours' if a is None else 'spec'}")
        elif (a["name"], a["store"], a["branch"]) != (b.name, b.store, b.branch):
            problems.append(f"{key}: spec {a['name']} st={a['store']} br={a['branch']} "
                            f"vs ours {b.name} st={b.store} br={b.branch}")
    return problems


RUNNERS = {"story": run_story_case, "compile_run": run_compile_run, "screen": run_screen,
           "save_restore": run_save_restore, "compile_error": run_compile_error,
           "reject": run_reject, "reject_truncated": run_reject_truncated,
           "disasm": run_disasm, "audit": run_audit, "spec_opcodes": run_spec_opcodes}


def main(argv: list[str]) -> int:
    cases = json.loads((ROOT / "eval" / "cases.json").read_text())["cases"]
    if argv:
        cases = [c for c in cases if any(word in c["id"] for word in argv)]
    failed = skipped = 0
    for case in cases:
        try:
            problems = RUNNERS[case["type"]](case)
        except Skip as why:
            print(f"SKIP  {case['id']:<28} {why}")
            skipped += 1
            continue
        except Exception as exc:                       # a crash is a failure
            problems = [f"crashed: {type(exc).__name__}: {exc}"]
        if problems:
            failed += 1
            print(f"FAIL  {case['id']:<28} " + "; ".join(problems[:4]))
        else:
            print(f"PASS  {case['id']}")
    print(f"\n{len(cases) - failed - skipped} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
