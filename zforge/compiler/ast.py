"""The typed AST produced by forms.py.

Declarations (top level):  Constant Global Object PropDef Routine
                           Syntax, verb/prep synonyms (grammar.py turns
                           these into constants + tables before semantics)
Expressions (inside routines):
    Num Str Local Global Word False_ Atom      values
    Call(name, args)                           any <NAME args...> form
    Cond Repeat Do MapContents Prog Tell Table Zop   forms with special syntax
Everything else - arithmetic, predicates, SET, MOVE, PRINTN, ... - is a
plain Call; codegen.py looks the name up in its table of built-ins.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from zforge.compiler.diagnostics import Location


# ------------------------------------------------------------ expressions
@dataclass
class Num:
    value: int
    loc: Location


@dataclass
class Str:
    value: str
    loc: Location


@dataclass
class Local:              # .X
    name: str
    loc: Location


@dataclass
class Global:             # ,X  - a global, constant, object, routine, flag, P?prop
    name: str
    loc: Location


@dataclass
class Word:               # W?WORD - a dictionary word
    word: str
    loc: Location


@dataclass
class False_:             # <>
    loc: Location


@dataclass
class Atom:               # a bare atom: T, ELSE, CR, a variable name after SET...
    name: str
    loc: Location


@dataclass
class Call:
    name: str
    args: list
    loc: Location


@dataclass
class Cond:
    clauses: list         # [(test or None for ELSE/T, [body exprs])]
    loc: Location


@dataclass
class Repeat:
    bindings: list        # [(local name, init expr or None)]
    body: list
    loc: Location


@dataclass
class Do:                 # <DO (I start end [step]) body...>
    var: str
    start: object
    end: object
    step: int
    body: list
    loc: Location


@dataclass
class MapContents:        # <MAP-CONTENTS (I container) body...>
    var: str
    container: object
    body: list
    loc: Location


@dataclass
class Prog:               # <PROG (bindings) body...>  or  <BIND (bindings) body...>
    kind: str             # "PROG" (a RETURN/AGAIN target) | "BIND" (scope only)
    bindings: list        # [(local name, init expr or None)]
    body: list
    loc: Location


@dataclass
class Tell:
    items: list           # [("str", text) | ("cr",) | ("num"|"obj"|"char"|"paddr", expr)]
    loc: Location


@dataclass
class Table:              # TABLE / LTABLE / ITABLE
    kind: str             # "TABLE" | "LTABLE" | "ITABLE"
    byte: bool
    items: list           # TABLE/LTABLE items, or [count, init] for ITABLE
    loc: Location


@dataclass
class Zop:                # <ZOP opcode-name args...> - raw §15 opcode
    opcode: str
    args: list
    loc: Location


# ------------------------------------------------------------ declarations
@dataclass
class ConstantDecl:
    name: str
    value: object
    loc: Location


@dataclass
class GlobalDecl:
    name: str
    init: object
    loc: Location


@dataclass
class PropValue:
    kind: str             # "to" (exit to a room: 1 byte) | "words"
    values: list
    loc: Location


@dataclass
class ObjectDecl:
    name: str
    is_room: bool
    loc: Location
    parent: str | None = None
    desc: str | None = None
    flags: list = field(default_factory=list)          # [(name, loc)]
    synonyms: list = field(default_factory=list)       # [str]
    adjectives: list = field(default_factory=list)     # [str]
    properties: list = field(default_factory=list)     # [(name, PropValue)]


@dataclass
class PropDefDecl:
    name: str
    default: object
    loc: Location


@dataclass
class RoutineDecl:
    name: str
    params: list          # required argument names
    optionals: list       # [(name, default expr or None)]
    auxes: list           # [(name, default expr or None)]
    body: list
    loc: Location

    def local_names(self) -> list[str]:
        return self.params + [n for n, _ in self.optionals] + [n for n, _ in self.auxes]


@dataclass
class SyntaxDecl:
    """<SYNTAX verb [prep] [OBJECT [(FIND flag)]] [prep] [OBJECT ...] [prep]
               = ACTION [PREACTION]>"""
    verb: str
    objects: int          # 0, 1 or 2
    preps: list           # [prep before/after object 1, prep before object 2] (None = none)
    finds: list           # [FIND flag for object 1, for object 2]            (None = none)
    action: str
    preaction: str | None
    loc: Location
    options: list = field(default_factory=lambda: [set(), set()])  # search options per object


@dataclass
class SynonymDecl:        # <VERB-SYNONYM TAKE GET GRAB>  /  <PREP-SYNONYM IN INTO>
    kind: str             # "VERB" | "PREP"
    word: str
    synonyms: list
    loc: Location


@dataclass
class Program:
    version: int = 5
    constants: list = field(default_factory=list)
    globals: list = field(default_factory=list)
    objects: list = field(default_factory=list)
    propdefs: list = field(default_factory=list)
    directions: list = field(default_factory=list)
    routines: list = field(default_factory=list)
    syntaxes: list = field(default_factory=list)       # [SyntaxDecl]
    synonyms: list = field(default_factory=list)       # [SynonymDecl]
