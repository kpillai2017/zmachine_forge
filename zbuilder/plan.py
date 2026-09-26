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


# Tiers from here on belong to proforma v2; their tasks must ALSO keep the
# whole v1 eval suite green (the v1 cases are a contract).
V2_FIRST_TIER = 5

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
         ["zforge/compiler/", "zforge/lib/", "examples/cloak_syntax.zil",
          "examples/parser_demo.zil"], ["§13", "§12.4"],
         ["grammar-adventure-win", "grammar-parser-messages", "grammar-lose-in-dark",
          "prog-bind", "grammar-errors-reported", "parser-disambiguation",
          "parser-reply-is-new-command", "parser-pronouns", "parser-pronoun-out-of-scope",
          "parser-orphan-object", "parser-orphan-not-here", "parser-prefers-context"],
         ["tests/test_grammar.py"]),
    # ================================================================ v2
    # Proforma v2 (agentic_ai_proforma_v2_inform7_zmachine_filled.txt):
    # I7-lite -> ZIL-lite -> z5/z6/z7/z8. Tiers continue the v1 numbering;
    # every v2 tier ALSO requires the v1 eval suite to stay green.
    # ---- Tier 5: version-aware refactor with ZERO behaviour change
    # (V2_FIRST_TIER below: from here on the Verifier also runs the v1 suite)
    Task("v2-golden-baseline", 5, "Freeze today's build outputs (zbuilder golden)",
         ["zbuilder/tools/golden.py", "tests/golden/v1_hashes.json"], [],
         ["refactor-byte-identical"], []),
    Task("v2-opcode-versions", 5, "opcodes.json + opcodes.py per version (v7/v8 = v5 table, §1)",
         ["zbuilder/tools/opcode_table.py", "zforge/common/opcodes.py", "spec/opcodes.json"],
         ["§14", "§1", "§15 pull"], ["spec-opcode-versions", "spec-grounding"],
         ["tests/test_versions.py", "tests/test_opcode_table.py"]),
    Task("v2-version-profile", 5, "VersionProfile(5); route every v5 hard-code through it",
         ["zforge/common/versions.py", "zforge/common/header.py", "zforge/vm/machine.py",
          "zforge/asm/assembler.py", "zforge/asm/linker.py", "zforge/asm/disasm.py"],
         ["§1.1.4", "§1.2.3", "§5.4", "§5.5", "§11.1.6"],
         ["version-profile", "refactor-byte-identical", "reject-non-v5"],
         ["tests/test_versions.py"]),
    # ---- Tier 6: versions 7 and 8 (§1: "identical to Version 5 except
    # as stated at 1.1.4 and 1.2.3")
    Task("v2-profiles-7-8", 6, "VersionProfile(7), (8); header R_O/S_O; VM unpacking",
         ["zforge/common/versions.py", "zforge/common/header.py", "zforge/vm/machine.py",
          "zforge/asm/disasm.py", "zforge/asm/info.py"],
         ["§1", "§1.1.4", "§1.2.3", "§11.1.6"],
         ["version-profile", "status-line-per-target", "save-restore-per-target"],
         ["tests/test_versions.py"]),
    Task("v2-assemble-7-8", 6, "Assembler/linker: offsets, alignment, size check, --target",
         ["zforge/asm/assembler.py", "zforge/asm/linker.py", "zforge/config.py",
          "zforge/cli.py", "zforge/compiler/driver.py", "zforge/compiler/forms.py"],
         ["§1.1.4", "§1.2.3", "§6.4.3"],
         ["hello-asm-per-target", "compile-arith-per-target", "cross-version-cloak-zil",
          "target-setting", "story-size-limits"],
         ["tests/test_versions.py", "tests/test_config.py"]),
    Task("v2-decoder-per-version", 6, "Decoder uses table_for(version); reject v1-4 (exit 2)",
         ["zforge/vm/decoder.py", "zforge/cli.py"], ["§14", "§11.1.1"],
         ["illegal-opcode-per-version", "reject-below-v5", "reject-non-v5"],
         ["tests/test_cli.py"]),
    Task("v2-conformance-z8", 6, "czech.z8 conformance (skips until compiled)",
         ["zbuilder/tools/fetch_stories.py", "stories/urls.txt"], ["§1"],
         ["czech-conformance-z8", "czech-reference-z5"], []),
    Task("v2-play-real-z8", 6, "Real v8 games: Advent_Crowther (Inform 7) + Jigsaw (Inform 6)",
         ["stories/urls.txt", "eval/run_eval.py", "zforge/vm/screen/plain.py",
          "zforge/vm/screen/base.py"], ["§1.2.3", "§8", "Quetzal"],
         ["play-real-z8-advent", "play-real-z8-jigsaw"], ["tests/test_screen.py"]),
    # ---- Tier 7: the I7-lite compiler (docs/I7_LITE.md, docs/I7_TO_ZIL.md)
    Task("v2-i7-hello", 7, "I7-lite pipeline + runtime: Hello World on z5, z7, z8",
         ["zforge/compiler/i7/", "zforge/lib/i7/", "zforge/cli.py", "examples/hello.ni"],
         ["§1.2.3", "§12", "§15"], ["hello-i7"], ["tests/test_i7.py"]),
    Task("v2-i7-cloak", 7, "Cloak of Darkness in Inform 7: rules, darkness, scoring, endings",
         ["zforge/compiler/i7/", "zforge/lib/i7/", "zforge/lib/parser.zil",
          "examples/cloak.ni"], ["§12", "§15"],
         ["cloak-i7-win", "cloak-i7-lose", "i7-parser-messages"], ["tests/test_i7.py"]),
    Task("v2-i7-problems", 7, "Inform 7-style problem messages for broken sources",
         ["zforge/compiler/i7/problems.py", "tests/samples/broken.ni"], [],
         ["i7-problems"], ["tests/test_i7.py"]),
    Task("v2-i7-7b", 7, "I7-lite 7b: the survey's features (doors, keys, devices, "
         "'is usually', articles, names, synonyms, presence)",
         ["zforge/compiler/i7/", "zforge/lib/i7/", "tests/samples/doors_and_lamps.ni"],
         ["I7_LITE.md", "I7_SURVEY.md"], ["i7-doors-devices"], ["tests/test_i7.py"]),
    Task("v2-i7-7c", 7, "I7-lite 7c: adaptive text, fixed viewpoint ([We] [are] "
         "[regarding X], the story's own verbs)",
         ["zforge/compiler/i7/", "zforge/lib/i7/say.zil", "tests/samples/adaptive.ni"],
         ["I7_LITE.md"], ["i7-adaptive-text"], ["tests/test_i7.py"]),
    Task("v2-i7-rules", 7, "I7-lite: Inform 7's named library rules, rule swapping, "
         "response edits; Advent's opening matches the real game (ADR-028)",
         ["zforge/compiler/i7/", "zforge/lib/i7/", "examples/advent_opening.ni",
          "eval/differential.py"],
         ["I7_LITE.md", "ADR-028"], ["i7-advent-differential"], ["tests/test_i7.py"]),
]


def tiers(plan: list[Task] | None = None) -> dict[int, list[Task]]:
    out: dict[int, list[Task]] = {}
    for task in plan or DEFAULT_PLAN:
        out.setdefault(task.tier, []).append(task)
    return dict(sorted(out.items()))


def find(task_id: str) -> Task | None:
    return next((t for t in DEFAULT_PLAN if t.id == task_id), None)
