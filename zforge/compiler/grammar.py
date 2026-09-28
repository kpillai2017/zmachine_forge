"""Stage 3b - grammar: SYNTAX lines become DATA.

Infocom's compiler did not "understand" English. A SYNTAX line such as

    <SYNTAX PUT OBJECT IN OBJECT = V-PUT-IN>

only produced a table row; the parser in the game's own ZIL code (see
zforge/lib/parser.zil) walked that table at run time. We do the same, by
DESUGARING the grammar into ordinary declarations the later stages already
know how to compile:

  * one constant per action:  V-PUT-IN  ->  <CONSTANT V?PUT-IN n>   (n = 1, 2, ...)
  * field offsets:            <CONSTANT S-VERB 0> ... <CONSTANT S-SIZE 11>
  * search-option bits:       <CONSTANT SO-HELD 1> <CONSTANT SO-ROOM 2> <CONSTANT SO-INSIDE 4>
  * <GLOBAL SYNTAX-TABLE <TABLE count  entry1...  entry2... >>

Each entry is S-SIZE (11) words:

    S-VERB      the verb's dictionary word         (W?PUT)
    S-NOBJ      number of OBJECT slots             (0, 1 or 2)
    S-PREP1     word before object 1, or the particle of a 0-object verb (or 0)
    S-PREP2     word before object 2, or a trailing particle              (or 0)
    S-FIND1     (FIND flag) attribute for object 1, -1 if none
    S-FIND2     (FIND flag) attribute for object 2, -1 if none
    S-OPTS1     search-option bits for object 1 (SO-HELD | SO-ROOM | SO-INSIDE)
    S-OPTS2     search-option bits for object 2
    S-ACTION    the action number (V?PUT-IN)
    S-ROUTINE   the action routine    (packed address, call with APPLY)
    S-PREACTION the preaction routine, or 0

VERB-SYNONYM and PREP-SYNONYM simply add more rows: one per combination of
synonyms. Words used in the table go into the dictionary automatically.
See docs/DECISIONS.md ADR-016.
"""
from __future__ import annotations

from itertools import product

from zforge.compiler import ast
from zforge.compiler.diagnostics import Diagnostics

FIELDS = ["S-VERB", "S-NOBJ", "S-PREP1", "S-PREP2", "S-FIND1", "S-FIND2",
          "S-OPTS1", "S-OPTS2", "S-ACTION", "S-ROUTINE", "S-PREACTION"]

# ZIL search options -> the preference bit the parser library understands.
# INSIDE-PRSI is a zforge extension (not in Infocom's ZIL): "prefer objects
# inside the indirect object", for TAKE KEY FROM BOX. See ADR-019.
# MANY (Infocom's): object 1 may be several things - TAKE ALL, DROP A AND B.
# Only the I7 runtime's parser acts on it (ADR-035).
# TOPIC (zforge's, for Inform's [text]): the slot takes any words, not a thing.
# REVERSED (zforge's, for Inform's "(with nouns reversed)"), on object 1: the
# thing typed first is the second noun (GIVE BEAST ROSE = give the rose to him).
BITS = {"SO-HELD": 1, "SO-ROOM": 2, "SO-INSIDE": 4, "SO-MANY": 8, "SO-TOPIC": 16,
        "SO-REVERSED": 32, "SO-TEST": 64}
OPTION_BITS = {"HELD": "SO-HELD", "CARRIED": "SO-HELD", "HAVE": "SO-HELD",
               "ON-GROUND": "SO-ROOM", "IN-ROOM": "SO-ROOM", "INSIDE-PRSI": "SO-INSIDE",
               "MANY": "SO-MANY", "TOPIC": "SO-TOPIC", "REVERSED": "SO-REVERSED", "TEST": "SO-TEST"}
TABLE_NAME = "SYNTAX-TABLE"
NO_FIND = -1


def action_constant(routine: str) -> str:
    """V-TAKE -> V?TAKE   (a routine not called V-... keeps its whole name)."""
    return "V?" + (routine[2:] if routine.startswith("V-") else routine)


def desugar(program: ast.Program, diag: Diagnostics) -> None:
    """Replace program.syntaxes/synonyms with constants and SYNTAX-TABLE."""
    if not program.syntaxes:
        for s in program.synonyms:
            diag.error(s.loc, f"{s.kind}-SYNONYM {s.word.upper()} without any SYNTAX")
        return

    # Collect verb and preposition synonyms, and assign action numbers.
    verb_syns, prep_syns = _synonyms(program, diag)
    actions = _action_numbers(program, diag)
    loc = program.syntaxes[0].loc

    # Define field offset constants: S-VERB, S-NOBJ, S-PREP1, etc.
    for i, name in enumerate(FIELDS):
        program.constants.append(ast.ConstantDecl(name, ast.Num(i, loc), loc))
    program.constants.append(ast.ConstantDecl("S-SIZE", ast.Num(len(FIELDS), loc), loc))

    # Define search-option bits: SO-HELD, SO-ROOM, SO-INSIDE, SO-MANY.
    for name, bit in BITS.items():
        program.constants.append(ast.ConstantDecl(name, ast.Num(bit, loc), loc))

    # Define action constants: V?TAKE, V?DROP, etc., one per unique action.
    for name, (number, where) in actions.items():
        program.constants.append(ast.ConstantDecl(name, ast.Num(number, where), where))

    # Validate that each SYNTAX's action and preaction routines exist.
    routines = {r.name for r in program.routines}
    rows: list[list] = []
    for s in program.syntaxes:
        missing = [n for n in (s.action, s.preaction) if n and n not in routines]
        for name in missing:
            diag.error(s.loc, f"SYNTAX {s.verb.upper()}: routine {name} is not defined")
        if missing:
            continue

        # For each preposition variant, emit a row per verb x preposition combination.
        preps = [[p] + prep_syns.get(p, []) if p else [None] for p in s.preps]
        for verb, p1, p2 in product([s.verb] + verb_syns.get(s.verb, []), *preps):
            rows.append(_row(s, verb, p1, p2))

    # Build the SYNTAX-TABLE: a word table with row count followed by S-SIZE-word rows.
    items = [ast.Num(len(rows), loc)] + [item for row in rows for item in row]
    program.globals.append(ast.GlobalDecl(TABLE_NAME, ast.Table("TABLE", False, items, loc),
                                          loc))


def _row(s: ast.SyntaxDecl, verb: str, p1: str | None, p2: str | None) -> list:
    """Build one row of the SYNTAX-TABLE (S-SIZE words): verb, nobj, preps, finds,
    search options, action number, action routine, and preaction routine."""
    loc = s.loc

    # Helper to convert a word name to W?name, or 0 if no word.
    def word(w):
        return ast.Word(w, loc) if w else ast.Num(0, loc)

    # Helper to convert a FIND flag name to a global reference, or -1 if none.
    def find(flag):
        return ast.Global(flag, loc) if flag else ast.Num(NO_FIND, loc)

    # Helper to OR together the search-option bits.
    def bits(options):
        return ast.Num(sum({BITS[OPTION_BITS[o]] for o in options}), loc)

    # Return the row: [verb, nobj, prep1, prep2, find1, find2, opts1, opts2,
    # action_num, action_routine, preaction].
    return [word(verb), ast.Num(s.objects, loc), word(p1), word(p2),
            find(s.finds[0]), find(s.finds[1]), bits(s.options[0]), bits(s.options[1]),
            ast.Global(action_constant(s.action), loc), ast.Global(s.action, loc),
            ast.Global(s.preaction, loc) if s.preaction else ast.Num(0, loc)]


def _action_numbers(program: ast.Program, diag: Diagnostics) -> dict:
    """First-seen order: V?name -> (number, location)."""
    actions: dict[str, tuple[int, object]] = {}
    owner: dict[str, str] = {}
    for s in program.syntaxes:
        name = action_constant(s.action)
        # Check: does this V? constant already belong to a different routine?
        if name in owner and owner[name] != s.action:
            diag.error(s.loc, f"actions {owner[name]} and {s.action} would both be {name}")
            continue
        # First seen: assign the next action number.
        if name not in actions:
            actions[name] = (len(actions) + 1, s.loc)
            owner[name] = s.action
    return actions


def _synonyms(program: ast.Program, diag: Diagnostics) -> tuple[dict, dict]:
    """Collect verb and preposition synonyms, validating they match existing verbs/preps.

    Returns ({verb: [syn1, syn2, ...]}, {prep: [syn1, ...]}). Errors if a synonym
    refers to a word not used in any SYNTAX line.
    """
    # Find all verbs and prepositions used in SYNTAX lines.
    verbs = {s.verb for s in program.syntaxes}
    preps = {p for s in program.syntaxes for p in s.preps if p}
    verb_syns: dict[str, list] = {}
    prep_syns: dict[str, list] = {}

    # For each synonym, ensure the primary word is known, then add its synonyms.
    for syn in program.synonyms:
        known, table = (verbs, verb_syns) if syn.kind == "VERB" else (preps, prep_syns)
        if syn.word not in known:
            what = "verb" if syn.kind == "VERB" else "preposition"
            diag.error(syn.loc, f"{syn.kind}-SYNONYM {syn.word.upper()}: no SYNTAX uses "
                                f"the {what} {syn.word.upper()}")
            continue
        table.setdefault(syn.word, []).extend(w for w in syn.synonyms if w != syn.word)
    return verb_syns, prep_syns
