"""The default build plan: tiers of tasks (proforma Section 1c).

Each task names the files it owns, the spec sections the Spec Analyst
must brief, and the eval cases that decide "done". A tier is only
started when every task of the tier before it is DONE (the STOP rule).
The Architect agent may PROPOSE changes (build/plan/proposed.json);
they are never applied without a human.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Task:
    id: str
    tier: int
    title: str
    files: list[str]
    spec_refs: list[str]
    eval_cases: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


DEFAULT_PLAN: list[Task] = [
    # ---- Tier 0: walking skeleton
    Task("spec-grounding", 0, "Fetch + index the spec; extract the §14 opcode table",
         ["zbuilder/tools/fetch_spec.py", "zbuilder/tools/spec_index.py",
          "zbuilder/tools/opcode_table.py", "zforge/common/opcodes.py"],
         ["§14", "§14.1"], ["spec-grounding"], ["tests/test_opcode_table.py"]),
    Task("memory-header-text", 0, "Memory map, header, Z-string text encoding",
         ["zforge/common/memory.py", "zforge/common/header.py", "zforge/common/text.py",
          "zforge/common/numbers.py"],
         ["§1", "§2", "§3", "§11"], [], ["tests/test_text.py", "tests/test_numbers.py"]),
    Task("decoder-skeleton", 0, "Instruction decoder + minimal VM + hello world",
         ["zforge/vm/decoder.py", "zforge/vm/machine.py", "zforge/vm/frames.py"],
         ["§4", "§5", "§6"], ["reject-non-v5", "reject-truncated"], ["tests/test_decoder.py"]),
    # ---- Tier 1: the full interpreter
    Task("all-opcodes", 1, "Every v5 opcode handler, grouped by family",
         ["zforge/vm/ops/"], ["§15"], ["czech-conformance", "praxix-conformance",
                                      "strictz-no-crash", "readability-audit"],
         ["tests/test_vm_ops.py"]),
    Task("objects-dictionary", 1, "Object table and dictionary / tokenise",
         ["zforge/vm/objects.py", "zforge/vm/lexer.py"], ["§12", "§13"], [],
         ["tests/test_objects.py"]),
    Task("streams-screen", 1, "Output streams and the screen model",
         ["zforge/vm/streams.py", "zforge/vm/screen/"], ["§7", "§8", "§10"],
         ["status-line-upper-window"], ["tests/test_screen.py"]),
    Task("save-undo", 1, "Quetzal save/restore and undo",
         ["zforge/vm/quetzal.py", "zforge/vm/ops/misc.py"], ["§15 save", "§15 save_undo",
                                                             "Appendix C"],
         ["save-restore-quetzal", "undo"], ["tests/test_quetzal.py"]),
    # ---- Tier 2: assembler + compiler
    Task("assembler", 2, "Assembler, linker, disassembler",
         ["zforge/asm/"], ["§4", "§11", "§12", "§13"], ["disasm-shows-text"],
         ["tests/test_assembler.py"]),
    Task("zil-compiler", 2, "ZIL-lite: lexer, reader, forms, semantic, codegen",
         ["zforge/compiler/"], ["§15"], ["compile-hello", "compile-arith-edges",
                                         "compile-errors-reported"],
         ["tests/test_compiler.py"]),
    Task("mini-adventure", 2, "examples/cloak.zil plays start to finish",
         ["examples/cloak.zil"], ["§15 read", "§13"],
         ["mini-adventure-win", "mini-adventure-lose"], []),
    # ---- Tier 3: CLI + curses
    Task("cli-curses", 3, "zforge CLI; curses renderer of the screen model",
         ["zforge/cli.py", "zforge/vm/screen/curses_screen.py"], ["§8"], [],
         ["tests/test_cli.py"]),
    # ---- Tier 4: ZIL-lite grammar + blocks
    Task("zil-grammar", 4, "SYNTAX / VERB-SYNONYM / PREP-SYNONYM as data, PROG / BIND, "
         "the lib/parser.zil library (pronouns, 'which do you mean?', asking for a "
         "missing object, search-option preferences) and the examples",
         ["zforge/compiler/", "examples/lib/", "examples/cloak_syntax.zil",
          "examples/parser_demo.zil"], ["§13", "§12.4"],
         ["grammar-adventure-win", "grammar-parser-messages", "grammar-lose-in-dark",
          "prog-bind", "grammar-errors-reported", "parser-disambiguation",
          "parser-reply-is-new-command", "parser-pronouns", "parser-pronoun-out-of-scope",
          "parser-orphan-object", "parser-orphan-not-here", "parser-prefers-context"],
         ["tests/test_grammar.py"]),
]


def tiers(plan: list[Task] | None = None) -> dict[int, list[Task]]:
    out: dict[int, list[Task]] = {}
    for task in plan or DEFAULT_PLAN:
        out.setdefault(task.tier, []).append(task)
    return dict(sorted(out.items()))


def find(task_id: str) -> Task | None:
    return next((t for t in DEFAULT_PLAN if t.id == task_id), None)
