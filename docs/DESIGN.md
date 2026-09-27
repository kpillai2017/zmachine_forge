# How the pieces fit

A game travels from left to right. Inform 7 is first translated into ZIL,
ZIL is compiled into assembly, and assembly becomes the bytes of a story
file. The interpreter then runs those bytes, and the screen shows what the
game prints.

```
 Inform 7 (.ni) ──► compiler/i7 ──┐
                                  ▼
               ZIL (.zil) ──► compiler ──► assembly (.zas) ──► asm ──► story file (.z5 - .z8)
                                                                               │
                              disassembler ◄──────────────────────────────────┤
                                                                               ▼
                                                  interpreter (vm) ──► screen (curses or plain)
```

Two things are shared by everything, so no two parts can disagree: **one
opcode table** (`zforge/common/opcodes.py`, checked against section 14 of
the standard by a test) and **one text encoder** (`zforge/common/text.py`).
Everything that differs between versions 5, 6, 7 and 8 lives in one place,
`zforge/common/versions.py`; `python -m zforge info --versions` prints it
as a table.

The game's own library is written in ZIL, not Python: the parser
(`zforge/lib/parser.zil`) and Inform 7's standard rules
(`zforge/lib/i7/`). So the interpreter knows nothing about rooms, lamps or
parsing. It just runs instructions, the way a real Z-machine does.

## Where to start

If you read one thing, read [TOUR.md](TOUR.md). It follows the command
"take lamp" through every stage below, with the real output of each.

If compilers and interpreters are new to you, start one step earlier, with
[HOW_THE_COMPILER_WORKS.md](HOW_THE_COMPILER_WORKS.md) and
[HOW_THE_INTERPRETER_WORKS.md](HOW_THE_INTERPRETER_WORKS.md). They explain
the ideas behind each stage with a program small enough to follow by hand.

## A reading order

The machine itself:

1. `common/numbers.py`, `common/memory.py`, `common/header.py` - sections
   1, 2 and 11 of the standard; then `common/versions.py`, every rule that
   differs between versions (ADR-021)
2. `common/text.py` - section 3: how text is packed into the story file
3. `vm/decoder.py` - section 4: the four shapes an instruction can take
4. `vm/frames.py`, `vm/machine.py` - sections 5 and 6: routines, the stack,
   and the loop that fetches and carries out each instruction
5. `vm/ops/*.py` - section 15, one family of instructions per file;
   `vm/ops/__init__.py` lists them all
6. `vm/objects.py`, `vm/lexer.py` - sections 12 and 13: the object tree,
   and splitting what you type into dictionary words
7. `vm/streams.py`, `vm/screen/base.py` - sections 7 and 8.7: output and
   the two-window screen; `vm/screen/v6.py` and `vm/ops/v6.py` - section
   8.8, version 6's eight windows (ADR-030); `vm/screen/curses_screen.py`
   draws either kind (ADR-032)
8. `vm/quetzal.py` - appendix C: saved games and undo

Making story files:

9. `asm/syntax.py`, `asm/assembler.py`, `asm/linker.py` - assembly text to
   bytes
10. `compiler/lexer.py`, `reader.py`, `forms.py`, `grammar.py`,
    `semantic.py`, `codegen.py` - ZIL to assembly, one stage per file
    ([ZIL_SUBSET.md](ZIL_SUBSET.md))
11. `zforge/lib/parser.zil` - the parser, with `examples/cloak_syntax.zil`
    and `examples/parser_demo.zil` to try it on

Inform 7:

12. `compiler/i7/source.py` - cutting the source into sentences;
    `model.py` - building the world from them; `phrases.py` - rules and
    conditions; `lower.py` - writing it all out as ZIL; `standard.py` -
    Inform's actions and library rules by name
    ([I7_TO_ZIL.md](I7_TO_ZIL.md))
13. `zforge/lib/i7/*.zil` - the library those rules live in:
    `actions.zil` runs an action's rulebooks, `standard.zil` holds the
    rules themselves, `activities.zil` and `say.zil` do the printing,
    `testing.zil` the `rules`, `actions` and `tree` commands (ADR-038)

To watch a stage at work: `--trace FILE` when running a game,
`--emit-zil`, `--emit-asm`, `--emit-tokens` or `--emit-ast` when
compiling, and `--testing` for Inform's own commands while you play.

## The zbuilder workflow

A deterministic **Orchestrator** walks the tiered plan (`zbuilder/plan.py`)
and drives five roles:

| Agent | Kind | Job |
|---|---|---|
| Spec Analyst | tools + LLM Q&A | fetch/index the spec, extract §14, brief each task with cited passages |
| Architect | LLM | render the plan; propose changes to `build/plan/proposed.json` (never auto-applied) |
| Implementer | LLM | write whole files for one task, only inside that task's scope; offline: write a brief |
| Verifier | tools (+ LLM diagnosis) | ruff, pytest, eval cases decide pass/fail; the LLM only explains failures |
| Reviewer | audit + LLM judge | readability rules (short functions, § citations, no eval/bare except) |

Loops are bounded (3 attempts per task, `ZB_MAX_CALLS` LLM calls per run),
a tier starts only when the previous one is DONE, and every step is logged
to `build/logs/run-*.jsonl`.
