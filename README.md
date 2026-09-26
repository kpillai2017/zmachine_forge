# zmachine_forge

![CI](https://github.com/OWNER/zmachine_forge/actions/workflows/ci.yml/badge.svg)

A **study-friendly Z-machine toolchain (versions 5, 6, 7 and 8)** in plain Python, built from the
[Z-Machine Standards Document 1.1](https://inform-fiction.org/zmachine/standards/z1point1/index.html):

| | |
|---|---|
| **interpreter** | versions 5, 6, 7 and 8 (every rule that differs lives in `zforge/common/versions.py`); every opcode of both tables, object tree, dictionary, output streams, Quetzal save/restore, undo, and both screen models: §8.7's upper/lower windows and **version 6's eight windows** with margins, scrolling and window properties, one character to the unit (ADR-030). Passes `czech.z5` and `czech.z8` (406/406, and the print tests match the author's reference output) and `praxix.z5`; plays the real v8 games *Adventure* (Inform 7 port, 431 KB) and *Jigsaw* (Inform 6, 305 KB), incl. save/restore/undo |
| **compiler** | **Inform 7-lite** (`.ni`, docs/I7_LITE.md) and **ZIL-lite** (a documented subset of Infocom's ZIL, incl. SYNTAX grammar and PROG/BIND) -> `.zas` assembly -> `.z5`, `.z6`, `.z7` or `.z8` (`--target`) |
| **assembler / disassembler** | readable `.zas` text, branch relaxation, linker, checksum; recursive-descent disassembler and `info` dumps |
| **CLI** | curses terminal UI (status line, reverse video, colours) or plain text for pipes |
| **zbuilder** | the agentic workflow that plans, briefs, verifies and reviews the build |

Readability beats speed everywhere: names follow the spec, every opcode
handler's docstring cites its §15 entry, and `zforge spec TERM` looks the
spec up offline.

## Setup (pyenv + direnv - nothing is installed for you)

```bash
cd zmachine_forge
direnv allow                 # .envrc: `use python 3.13` + PYTHONPATH
pip install -r requirements.txt   # dev only: pytest, ruff (the code is stdlib-only)
cp .env.example .env         # only needed for zbuilder with an LLM
```

## Play

```bash
./start.sh                                   # compile + play examples/cloak.zil
python -m zforge run stories/czech.z5        # any v5 story (curses when on a terminal)
python -m zforge run game.z5 --ui plain --script moves.txt --transcript log.txt
```

## Compile and inspect

```bash
python -m zforge compile examples/cloak.zil -o build/cloak.z5 --emit-asm --emit-tokens --emit-ast
python -m zforge compile examples/cloak_syntax.zil -o build/cloak_syntax.z5 --emit-asm   # SYNTAX + lib/parser
python -m zforge compile examples/parser_demo.zil -o build/parser_demo.z5 && python -m zforge run build/parser_demo.z5
python -m zforge asm tests/samples/hello.zas -o build/hello.z5
python -m zforge compile examples/cloak.zil --target z8 -o build/cloak.z8   # or z6, z7; see below
python -m zforge disasm build/cloak.z5
python -m zforge info build/cloak.z5 --objects
```

**Choosing the version.** `--target z5|z6|z7|z8`, else `target = "z8"` in a
`zforge.toml` in the current directory, else the `ZFORGE_TARGET` environment
variable, else the source's own `<VERSION>` (z5 for `.zas`). The build line
says which one applied, e.g. `target z8 from --target`. Versions 7 and 8 differ
from 5 only in story size and packed addresses (Standard §1), and version 6
adds eighteen opcodes and its window model without removing anything, so every
v5 program builds for all four: `python -m eval.run_eval cross-version` checks
that `cloak.zil` tells the same story on each.

Version 6 is Infocom's graphical Z-machine. zforge runs it on a character
terminal by making one unit one character, so all eight windows, their
margins and their properties work, but there are no pictures, mouse or
menus - the header says so, and ADR-030 explains the choice:

```bash
python -m zforge compile examples/v6_windows.zil -o build/v6.z6
python -m zforge run build/v6.z6 --ui curses      # a panel, a status bar, flowing text
```

```bash
python -m zforge spec print_char            # or: 3.8.5.3, "packed address"
```

## The build workflow (zbuilder)

```bash
python -m zbuilder spec        # fetch + index the Standard, extract the §14 opcode table
python -m zbuilder stories     # download czech/praxix/strictz (checksums pinned)
python -m zbuilder status      # tiered plan and each task's state
python -m zbuilder build       # the agent loop (offline = briefs + verification)
python -m zbuilder review      # readability / spec-citation audit
python -m zbuilder ask "how are branch offsets encoded?"
```

With no provider configured zbuilder runs **offline**: it verifies each
task with real tools, and for anything failing it writes a self-contained
brief to `build/tasks/<task>.md` that you can hand to Rovo Dev. With
`ZB_PROVIDER=rovodev` (or anthropic/openai/gemini/ollama) the Implementer
writes code itself; the Verifier's tools still decide pass/fail.

## Quality gates

```bash
ruff check .
pytest -q                      # 71 unit tests
python -m eval.run_eval        # 28 acceptance cases (proforma Section 1b)
```

## Read the code in this order

See [docs/DESIGN.md](docs/DESIGN.md). The ZIL-lite language is in
[docs/ZIL_SUBSET.md](docs/ZIL_SUBSET.md); spec interpretations are in
[docs/DECISIONS.md](docs/DECISIONS.md); what's missing is in
[docs/KNOWN_GAPS.md](docs/KNOWN_GAPS.md).

Test stories are downloaded, never committed - check each licence before
redistributing. The spec text is © its authors; only a local cache is kept.
