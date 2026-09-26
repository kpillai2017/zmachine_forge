# Design

```
            ZIL source ──► compiler ──► .zas text ──► assembler ──► .z5 ──► interpreter ──► screen
                           (5 stages)                 (+ linker)            (VM + ops)      (grid → curses / plain)
                                                                 ▲
                                               disassembler ◄────┘  (same decoder as the VM)
```

Everything shares **one opcode table** (`zforge/common/opcodes.py`,
checked against the spec's §14 by a test) and **one text encoder**
(`zforge/common/text.py`), so the compiler, assembler, disassembler and VM
can never disagree about an opcode or a z-string.

## Suggested study order

1. `common/numbers.py`, `common/memory.py`, `common/header.py` - §1, §2, §11;
   `common/versions.py` - every rule that differs between versions (ADR-021)
2. `common/text.py` - §3: z-characters, alphabets, ZSCII, Unicode
3. `vm/decoder.py` - §4: the four instruction forms
4. `vm/frames.py`, `vm/machine.py` - §5, §6: routines, the stack, the fetch-decode-execute loop
5. `vm/ops/*.py` - §15, one family per file; `vm/ops/__init__.py` is the explicit dispatch table
6. `vm/objects.py`, `vm/lexer.py` - §12, §13
7. `vm/streams.py`, `vm/screen/base.py` - §7, §8.7 (one grid model; `curses_screen.py` just draws it)
   `vm/screen/v6.py` - §8.8: version 6's eight windows, in front of that grid (ADR-030)
   `vm/screen/curses_screen.py` - draws either model; resizing and signals (ADR-032)
   `vm/ops/v6.py` - §15: the eighteen opcodes version 6 adds
8. `vm/quetzal.py` - Appendix C save files and undo
9. `asm/syntax.py` → `asm/assembler.py` → `asm/linker.py` - text to bytes
10. `compiler/lexer.py` → `reader.py` → `forms.py` → `grammar.py` → `semantic.py` → `codegen.py`
11. `zforge/lib/parser.zil` + `examples/cloak_syntax.zil` - the run-time half of SYNTAX;
    `examples/parser_demo.zil` exercises pronouns and "which do you mean?"

Run anything with `--trace FILE` (interpreter) or `--emit-asm --emit-tokens
--emit-ast` (compiler) to watch each stage.

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
