"""The eval harness: runs every case in eval/cases.json and prints one
PASS / FAIL / SKIP line each. Exit status 1 if anything FAILED.

    python -m eval.run_eval            # all cases
    python -m eval.run_eval undo czech # only cases whose id contains a word
    python -m eval.run_eval --suite v1 # only the zforge v1 cases (the regression gate)
    python -m eval.run_eval --suite v2 # only the cases added by proforma v2

A case without a "suite" key belongs to v1. "v1 suite still green" is a
gate for every v2 tier: the v1 cases are a contract.

Story-file cases SKIP (not fail) when the story isn't downloaded yet:
run `python -m zbuilder stories` first.
"""
from __future__ import annotations

import functools
import inspect
import json
import re
import subprocess
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


def _compile(path: str, target: int | None = None) -> bytes:
    src = ROOT / path            # absolute, so INSERT-FILE resolves from any cwd
    if src.suffix == ".ni":      # Inform 7 (I7-lite)
        from zforge.compiler.i7.driver import compile_i7
        return compile_i7(src.read_text(), str(src), target).story
    return compile_zil(src.read_text(), str(src), target).story


def _check_text(case: dict, text: str) -> list[str]:
    problems = [f"missing {s!r}" for s in case.get("must_contain", []) if s not in text]
    problems += [f"unexpected {s!r}" for s in case.get("must_not_contain", []) if s in text]
    if "must_contain_in_order" in case:           # e.g. restored, THEN the lamp is back
        at = 0
        for piece in case["must_contain_in_order"]:
            found = text.find(piece, at)
            if found < 0:
                problems.append(f"missing {piece!r} after position {at} (in-order check)")
                break
            at = found + len(piece)
    if "must_contain_lines" in case:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        want = case["must_contain_lines"]
        if lines[:len(want)] != want:
            problems.append(f"lines were {lines[:len(want)]}, expected {want}")
    return problems


def run_story_case(case: dict) -> list[str]:
    path = ROOT / case["story"]
    if not path.exists():
        raise Skip(case.get("skip_hint") or
                   f"{case['story']} not downloaded (python -m zbuilder stories)")
    with tempfile.TemporaryDirectory() as tmp:        # for {save_file} in scripts
        save_file = str(Path(tmp) / "game.qzl")
        script = [line.replace("{save_file}", save_file) for line in case.get("script", [])]
        result = play(path.read_bytes(), script)
    problems = _check_text(case, result.transcript + "\n" + result.reason)
    if "matches_file" in case:
        problems += _compare_with_reference(case, result.transcript)
    return problems


def _without_block(lines: list[str], start: str | None, end: str | None) -> list[str]:
    """Drop the lines from the one starting with `start` up to (not including)
    the one starting with `end` - e.g. an interpreter-specific header report."""
    if not start:
        return lines
    out, skipping = [], False
    for line in lines:
        if line.startswith(start):
            skipping = True
        elif skipping and end and line.startswith(end):
            skipping = False
        if not skipping:
            out.append(line)
    return out


def _compare_with_reference(case: dict, transcript: str) -> list[str]:
    """Compare with an expected-output file shipped with a test suite (e.g.
    czech.out8), ignoring the block the case names as interpreter-specific."""
    ref_path = ROOT / case["matches_file"]
    if not ref_path.exists():
        raise Skip(f"{case['matches_file']} not downloaded (python -m zbuilder stories)")
    start, end = case.get("ignore_from"), case.get("ignore_until")
    want = _without_block(ref_path.read_text(encoding="latin-1").replace("\r", "").splitlines(),
                          start, end)
    got = _without_block(transcript.splitlines(), start, end)
    want, got = [w.rstrip() for w in want], [g.rstrip() for g in got]
    for n, (w, g) in enumerate(zip(want, got, strict=False)):
        if w != g:
            return [f"differs from {case['matches_file']} at line {n + 1}: {g!r} != {w!r}"]
    if len(want) != len(got):
        return [f"{len(got)} lines, {case['matches_file']} has {len(want)}"]
    return []


def run_compile_run(case: dict) -> list[str]:
    result = play(_compile(case["source"], case.get("target")), case.get("script", []))
    return _check_text(case, result.transcript + "\n" + result.reason)


def run_screen(case: dict) -> list[str]:
    result = play(_compile(case["source"], case.get("target")), case.get("script", []))
    rows = result.screen.rows
    row0 = "".join(c.char for c in rows[0])
    problems = [f"status row lacks {s!r}: {row0!r}" for s in case["row0_contains"] if s not in row0]
    if case.get("row0_reverse") and not all(c.style & 1 for c in rows[0]):
        problems.append("status row is not entirely reverse video")
    return problems


def run_v6_windows(case: dict) -> list[str]:
    """§8.8: a version-6 story draws into several windows at once. The grid
    is checked row by row, so the panel really is beside the text."""
    result = play(_compile(case["source"], case.get("target")), case.get("script", []))
    rows = result.screen.text_rows()
    problems = []
    for want in case.get("rows_matching", []):
        if not any(re.search(want, row) for row in rows):
            problems.append(f"no row matches {want!r}")
    for number, want in case.get("row", {}).items():
        row = rows[int(number)] if int(number) < len(rows) else ""
        if not re.search(want, row):
            problems.append(f"row {number} is {row!r}, wanted {want!r}")
    windows = getattr(result.screen, "windows", [])
    for number, properties in case.get("window_properties", {}).items():
        for name, value in properties.items():
            actual = getattr(windows[int(number)], name, None)
            if actual != value:
                problems.append(f"window {number} {name} is {actual}, wanted {value}")
    return problems


def run_save_restore(case: dict) -> list[str]:
    """Real §15 save/restore opcodes through the game's SAVE/RESTORE verbs."""
    story = _compile(case["source"], case.get("target"))
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


def run_i7_problems(case: dict) -> list[str]:
    """A broken Inform 7 source: every problem reported, Inform 7 style, at its line."""
    from zforge.compiler.i7.driver import compile_i7
    src = ROOT / case["source"]
    try:
        compile_i7(src.read_text(), str(src))
    except ZForgeError as exc:
        text = str(exc)
        problems = [f"no problem reported at line {n}" for n in case["expect_lines"]
                    if f"{src.name}:{n}: Problem. You wrote" not in text]
        if "Traceback" in text:
            problems.append("a Python traceback leaked into the problems")
        return problems + _check_text(case, text)
    return ["compiled without problems"]


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


def run_golden(case: dict) -> list[str]:
    """refactor-byte-identical: today's outputs == the recorded v1 outputs."""
    from zbuilder.tools.golden import GOLDEN_FILE, check
    if not GOLDEN_FILE.exists():
        raise Skip("no golden hashes recorded (python -m zbuilder golden --record)")
    return check()


def run_pytest(case: dict) -> list[str]:
    """Run a selection of unit tests as one eval case (no duplicated logic)."""
    tests = case["tests"]
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    cmd += tests if isinstance(tests, list) else [tests]      # a file, or named tests
    if case.get("select"):
        cmd += ["-k", case["select"]]
    done = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300)
    if done.returncode == 0:
        return []
    failed = [line for line in done.stdout.splitlines() if line.startswith("FAILED")]
    return failed or [done.stdout.strip().splitlines()[-1] if done.stdout.strip() else
                      f"pytest exited {done.returncode}"]


# ------------------------------------------------ proforma v2, Tier 6 runners
def run_asm_run(case: dict) -> list[str]:
    """hello-asm per target: assemble, check the header, run, disassemble."""
    from zforge.asm.assembler import assemble
    from zforge.asm.disasm import disassemble
    from zforge.asm.info import header_report
    src = ROOT / case["source"]
    story = assemble(src.read_text(), str(src), case["target"])
    problems = []
    if story[0] != case["target"]:
        problems.append(f"header version byte is {story[0]}")
    if "(ok)" not in header_report(story):
        problems.append("checksum does not match")
    problems += [f"disasm lacks {s!r}" for s in case.get("disasm_contains", [])
                 if s not in disassemble(story)]
    result = play(story, case.get("script", []))
    return problems + _check_text(case, result.transcript + "\n" + result.reason)


def run_reject_cli(case: dict) -> list[str]:
    """The CLI refuses a story of an unsupported version: message + exit code."""
    import contextlib
    import io
    from zforge.cli import main as zforge_main
    story = bytearray(_compile("examples/hello.zil"))
    story[0] = case["version_byte"]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "old.z3"
        path.write_bytes(bytes(story))
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = zforge_main(["run", str(path), "--ui", "plain"])
    problems = [] if case["expect"] in err.getvalue() else [f"message was {err.getvalue()!r}"]
    if code != case["exit_code"]:
        problems.append(f"exit code {code}, expected {case['exit_code']}")
    if "Traceback" in err.getvalue():
        problems.append("traceback")
    return problems


def run_illegal_opcode(case: dict) -> list[str]:
    """Patch the first instruction of main into an opcode the version lacks."""
    from zforge.common.header import Header
    from zforge.vm.machine import ZMachine
    from zforge.vm.screen.virtual import VirtualScreen
    story = bytearray(_compile("examples/hello.zil", case["target"]))
    h = Header.parse(story)
    main = h.profile.unpack_routine(int.from_bytes(story[h.initial_pc + 2:h.initial_pc + 4],
                                                   "big"), h.routines_offset)
    first = main + 1                                   # after the locals count (v5+)
    story[first:first + 3] = bytes([0xBE, case["ext_number"], 0xFF])  # EXT n, no operands
    try:
        ZMachine(bytes(story), VirtualScreen()).run()
    except ZForgeError as exc:
        return [] if case["expect"] in str(exc) else [f"message was {exc}"]
    return ["the illegal opcode was executed"]


def run_cross_version(case: dict) -> list[str]:
    """The same source, built for several versions, must tell the same story."""
    transcripts = {t: play(_compile(case["source"], t), case["script"]).transcript
                   for t in case["versions"]}
    first = case["versions"][0]
    problems = []
    for t, text in transcripts.items():
        if text != transcripts[first]:
            a, b = transcripts[first].splitlines(), text.splitlines()
            pairs = enumerate(zip(a, b, strict=False))        # stop at the shorter one
            n = next((i for i, (x, y) in pairs if x != y), min(len(a), len(b)))
            problems.append(f"z{t} differs from z{first} at line {n + 1}")
    return problems + _check_text(case, transcripts[first])


@functools.cache
def _reference_transcript(story: str, commands: tuple[str, ...]) -> str:
    """The real game's side, played once per run (it is the same for every target)."""
    return play((ROOT / story).read_bytes(), list(commands)).transcript


def run_i7_differential(case: dict) -> list[str]:
    """Our build of a port and the real Inform 7 game, the same commands:
    every response the same (eval/differential.py says how exactly)."""
    from eval.differential import differences, responses
    from zforge.compiler.i7.driver import compile_i7
    reference = ROOT / case["reference"]
    if not reference.exists():
        raise Skip(f"{case['reference']} not downloaded (python -m zbuilder stories)")
    commands, banner = case["commands"], case["banner"]
    real = responses(_reference_transcript(case["reference"], tuple(commands)), commands, banner)
    src = ROOT / case["source"]
    story = compile_i7(src.read_text(), str(src), target=case["target"]).story
    ours = responses(play(story, commands).transcript, commands, banner)
    if case.get("replies_only"):             # a port of one room: the game's own
        real[0] = ours[0] = []               # opening is not part of the check
    return differences(commands, real, ours)


RUNNERS = {"story": run_story_case, "compile_run": run_compile_run, "screen": run_screen,
           "save_restore": run_save_restore, "compile_error": run_compile_error,
           "reject": run_reject, "reject_truncated": run_reject_truncated,
           "disasm": run_disasm, "audit": run_audit, "spec_opcodes": run_spec_opcodes,
           "golden": run_golden, "pytest": run_pytest, "asm_run": run_asm_run,
           "reject_cli": run_reject_cli, "illegal_opcode": run_illegal_opcode,
           "cross_version": run_cross_version, "i7_problems": run_i7_problems,
           "i7_differential": run_i7_differential, "v6_windows": run_v6_windows}


def expand_targets(cases: list[dict]) -> list[dict]:
    """A case with "targets": [5, 7, 8] runs once per target, as id[z7] etc."""
    out = []
    for case in cases:
        for t in case.get("targets", [None]):
            out.append(case if t is None else {**case, "target": t, "id": f"{case['id']}[z{t}]"})
    return out


def main(argv: list[str]) -> int:
    cases = json.loads((ROOT / "eval" / "cases.json").read_text())["cases"]
    if "--suite" in argv:
        i = argv.index("--suite")
        suite = argv[i + 1] if i + 1 < len(argv) else "all"
        argv = argv[:i] + argv[i + 2:]
        if suite != "all":
            cases = [c for c in cases if c.get("suite", "v1") == suite]
    if argv:
        cases = [c for c in cases if any(word in c["id"] for word in argv)]
    failed = skipped = 0
    cases = expand_targets(cases)
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
