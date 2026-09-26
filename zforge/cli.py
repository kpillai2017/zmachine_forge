"""The `zforge` command line.

    zforge run STORY.z5 [--ui auto|curses|plain] [--script FILE] [--seed N]
                        [--transcript FILE] [--trace FILE]
    zforge compile GAME.zil [-o GAME.z5] [--emit-asm] [--emit-tokens] [--emit-ast]
    zforge compile GAME.ni  [-o GAME.z8] [--emit-zil] [--emit-asm]      (Inform 7, I7-lite)
    zforge asm GAME.zas [-o GAME.z5]
    zforge disasm STORY.z5 [--routine 0xADDR]
    zforge info STORY.z5 [--header] [--objects] [--dictionary]
    zforge spec TERM                  (look up the cached Z-Machine Standard)

Errors are printed as one clear message (no Python traceback) unless
--debug is given; the exit status is non-zero on any error.
"""
from __future__ import annotations

import argparse
import os
import pprint
import sys
from pathlib import Path

from zforge.common.errors import UnsupportedTarget, UnsupportedVersion, ZForgeError
from zforge.common.versions import DEFAULT_VERSION
from zforge.config import Target, resolve_target


def _read_story(path: str) -> bytes:
    p = Path(path)
    if not p.exists():
        raise ZForgeError(f"{path}: no such file")
    return p.read_bytes()


# ---------------------------------------------------------------- run
def cmd_run(args) -> int:
    from zforge.vm.machine import ZMachine

    story = _read_story(args.story)
    script = Path(args.script).read_text().splitlines() if args.script else None
    ui = args.ui
    if ui == "auto":
        ui = "curses" if sys.stdin.isatty() and sys.stdout.isatty() and script is None \
            and _curses_available() else "plain"
    trace_file = open(args.trace, "w") if args.trace else None

    def play(screen) -> tuple[str, list[str], list[str]]:
        vm = ZMachine(story, screen, seed=args.seed, transcript_path=args.transcript,
                      trace_file=trace_file)
        vm.save_name = Path(args.story).with_suffix(".qzl").name
        try:
            reason = vm.run()
        except ZForgeError as exc:
            screen.close("error")
            return f"error: {exc}", vm.recent_trace(), vm.warnings
        screen.close(reason)
        return reason, [], vm.warnings

    try:
        if ui == "curses":
            from zforge.vm.screen.curses_screen import run_with_curses
            reason, trace, warnings = run_with_curses(play)
        else:
            from zforge.vm.screen.plain import PlainScreen
            reason, trace, warnings = play(PlainScreen(width=args.width, script=script))
    finally:
        if trace_file:
            trace_file.close()
    if args.verbose:
        for w in warnings:
            print(f"warning: {w}", file=sys.stderr)
    if reason.startswith("error:"):
        print(f"\nzforge: {reason[7:]}", file=sys.stderr)
        if trace:
            print("last instructions executed:", file=sys.stderr)
            print("\n".join("  " + t for t in trace), file=sys.stderr)
        return 1
    return 0


def _curses_available() -> bool:
    try:
        import curses  # noqa: F401
        return True
    except ImportError:          # e.g. Windows without windows-curses
        return False


# ------------------------------------------------------------ compile
def _explicit_target(args) -> Target | None:
    """--target, zforge.toml or ZFORGE_TARGET; None lets the source decide."""
    target = resolve_target(args.target, source_default=0)
    return None if target.origin == "the source" else target


I7_SUFFIXES = (".ni", ".i7")


def cmd_compile(args) -> int:
    from zforge.compiler.driver import compile_zil

    src = Path(args.source)
    if not src.exists():
        raise ZForgeError(f"{args.source}: no such file")
    target = _explicit_target(args)
    if src.suffix.lower() in I7_SUFFIXES:
        return compile_inform7(args, src, target)
    result = compile_zil(src.read_text(), str(src), target.version if target else None)
    origin = target.origin if target else "the source"
    out = Path(args.output) if args.output else src.with_suffix(f".z{result.version}")
    out.write_bytes(result.story)
    extras = []
    if args.emit_asm:
        out.with_suffix(".zas").write_text(result.assembly)
        extras.append(out.with_suffix(".zas").name)
    if args.emit_tokens:
        text = "\n".join(f"{t.location.line}:{t.location.column}\t{t.kind.name}\t{t.text!r}"
                         for t in result.tokens)
        out.with_suffix(".tokens").write_text(text + "\n")
        extras.append(out.with_suffix(".tokens").name)
    if args.emit_ast:
        out.with_suffix(".ast").write_text(pprint.pformat(result.program, width=100) + "\n")
        extras.append(out.with_suffix(".ast").name)
    also = f" (+ {', '.join(extras)})" if extras else ""
    print(f"compiled {src} -> {out}  ({len(result.story)} bytes, "
          f"target z{result.version} from {origin}){also}")
    return 0


def compile_inform7(args, src: Path, target) -> int:
    """An Inform 7 (I7-lite) source: .ni -> ZIL-lite -> story (default z8)."""
    from zforge.compiler.i7.driver import DEFAULT_TARGET, compile_i7

    result = compile_i7(src.read_text(), str(src), target.version if target else None)
    origin = target.origin if target else f"the I7-lite default (z{DEFAULT_TARGET})"
    out = Path(args.output) if args.output else src.with_suffix(f".z{result.version}")
    out.write_bytes(result.story)
    extras = []
    if args.emit_zil:
        out.with_suffix(".zil").write_text(result.zil)
        extras.append(out.with_suffix(".zil").name)
    if args.emit_asm:
        out.with_suffix(".zas").write_text(result.compiled.assembly)
        extras.append(out.with_suffix(".zas").name)
    for note in result.notes:
        print(f"note: {note}")
    also = f" (+ {', '.join(extras)})" if extras else ""
    print(f"compiled {src} -> {out}  ({len(result.story)} bytes, "
          f"target z{result.version} from {origin}){also}")
    return 0


def cmd_asm(args) -> int:
    from zforge.asm.assembler import assemble

    src = Path(args.source)
    if not src.exists():
        raise ZForgeError(f"{args.source}: no such file")
    target = resolve_target(args.target, DEFAULT_VERSION)
    story = assemble(src.read_text(), str(src), target.version)
    out = Path(args.output) if args.output else src.with_suffix(f".z{target.version}")
    out.write_bytes(story)
    print(f"assembled {src} -> {out}  ({len(story)} bytes, {target.describe()})")
    return 0


def cmd_disasm(args) -> int:
    from zforge.asm.disasm import disassemble

    routine = int(args.routine, 0) if args.routine else None
    print(disassemble(_read_story(args.story), routine))
    return 0


def cmd_info(args) -> int:
    from zforge.asm import info
    from zforge.common.header import Header

    story = _read_story(args.story)
    Header.parse(story)                       # validates: v5 only, sane addresses
    everything = not (args.header or args.objects or args.dictionary)
    if args.header or everything:
        print("Header (§11):\n" + info.header_report(story))
    if args.objects or everything:
        print("Objects (§12):\n" + info.object_report(story))
    if args.dictionary or everything:
        print("Dictionary (§13):\n" + info.dictionary_report(story))
    return 0


def cmd_spec(args) -> int:
    """Offline look-up in the cached spec built by `python -m zbuilder spec`."""
    try:
        from zbuilder.tools.spec_index import SPEC_INDEX, SpecIndex
    except ImportError as exc:
        raise ZForgeError("the spec tools (zbuilder) are not importable from here") from exc
    if not SPEC_INDEX.exists():
        raise ZForgeError("no cached spec yet - run: python -m zbuilder spec")
    hits = SpecIndex().lookup(" ".join(args.term), k=args.k)
    if not hits:
        print("no matching passage in the cached spec")
        return 1
    for hit in hits:
        print(f"[{hit['locator']}]\n{hit['text']}\n")
    return 0


# --------------------------------------------------------------- main
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="zforge", description="A study-friendly Z-machine v5 "
                                "toolchain: interpreter, ZIL-lite compiler, assembler.")
    p.add_argument("--debug", action="store_true", help="show Python tracebacks")
    sub = p.add_subparsers(dest="command", required=True)

    r = sub.add_parser("run", help="play a .z5 story file")
    r.add_argument("story")
    r.add_argument("--ui", choices=["auto", "curses", "plain"], default="auto")
    r.add_argument("--script", help="file of input lines (one command per line)")
    r.add_argument("--seed", type=int, help="seed the random number generator")
    r.add_argument("--transcript", help="write output stream 2 to this file")
    r.add_argument("--trace", help="write every executed instruction to this file")
    r.add_argument("--width", type=int, default=80, help="screen width in plain mode")
    r.add_argument("-v", "--verbose", action="store_true", help="print VM warnings")
    r.set_defaults(func=cmd_run)

    c = sub.add_parser("compile",
                       help="compile ZIL-lite (.zil) or Inform 7 (.ni) source to a story file")
    c.add_argument("source")
    c.add_argument("-o", "--output")
    c.add_argument("--target", help="z5, z7 or z8 (default: zforge.toml, $ZFORGE_TARGET, "
                                    "then the source's <VERSION>)")
    c.add_argument("--emit-zil", action="store_true",
                   help="(Inform 7 sources) also write the generated ZIL-lite")
    c.add_argument("--emit-asm", action="store_true", help="also write the .zas assembly")
    c.add_argument("--emit-tokens", action="store_true", help="also write the token stream")
    c.add_argument("--emit-ast", action="store_true", help="also write the AST")
    c.set_defaults(func=cmd_compile)

    a = sub.add_parser("asm", help="assemble .zas to a story file")
    a.add_argument("source")
    a.add_argument("-o", "--output")
    a.add_argument("--target", help="z5, z7 or z8 (default: zforge.toml, $ZFORGE_TARGET, z5)")
    a.set_defaults(func=cmd_asm)

    d = sub.add_parser("disasm", help="disassemble a story file")
    d.add_argument("story")
    d.add_argument("--routine", help="address of one routine, e.g. 0x4f0")
    d.set_defaults(func=cmd_disasm)

    i = sub.add_parser("info", help="dump header, object tree and dictionary")
    i.add_argument("story")
    i.add_argument("--header", action="store_true")
    i.add_argument("--objects", action="store_true")
    i.add_argument("--dictionary", action="store_true")
    i.set_defaults(func=cmd_info)

    s = sub.add_parser("spec", help="look up the Z-Machine Standard (offline cache)")
    s.add_argument("term", nargs="+", help="an opcode name, a section like 3.8.5.3, or words")
    s.add_argument("-k", type=int, default=3, help="number of passages")
    s.set_defaults(func=cmd_spec)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (UnsupportedVersion, UnsupportedTarget) as exc:
        if args.debug:                    # exit 2: the INPUT is not something zforge handles
            raise
        print(f"zforge: {exc}", file=sys.stderr)
        return 2
    except ZForgeError as exc:
        if args.debug:
            raise
        print(f"zforge: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130
    except BrokenPipeError:
        # `zforge run game.z5 | head`: the reader stopped reading. That is not
        # our error, so stop quietly. Pointing stdout at /dev/null stops
        # Python's own final flush from failing again ("Exception ignored").
        # (The recipe from the Python docs, "Note on SIGPIPE".)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 0


if __name__ == "__main__":
    sys.exit(main())
