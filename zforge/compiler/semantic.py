"""Stage 4 - semantic analysis: build the symbol table and check every
reference BEFORE generating code.

ZIL's three ways of naming things are the classic source of bugs:
    .X   the value of LOCAL X        ,X   the value of GLOBAL/constant/object X
    X    a bare ATOM (only meaningful in some positions, e.g. <SET X 1>)
so most checks here produce messages like "X is a local; use .X".

Numbering decisions (recorded in docs/DECISIONS.md):
  * FLAGS become attributes 0..47 in first-seen order          (§12.3.1)
  * property names become property numbers 1..63 in first-seen order:
    DIRECTIONS first, then PROPDEFs, then as met in objects      (§12.4)
  * DESC is the object's SHORT NAME, not a property              (§12.4.1)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from zforge.common.opcodes import BY_NAME
from zforge.compiler import ast
from zforge.compiler.diagnostics import Diagnostics

MAX_ATTRIBUTES = 48
MAX_PROPERTIES = 63
MAX_LOCALS = 15
ENTRY_ROUTINE = "GO"

# Built-in forms: name -> (min args, max args); None = no upper limit
BUILTINS: dict[str, tuple[int, int | None]] = {
    # arithmetic
    "+": (1, None), "-": (1, None), "*": (1, None), "/": (2, None), "MOD": (2, 2),
    "BAND": (2, None), "BOR": (2, None), "BCOM": (1, 1), "RANDOM": (1, 1),
    # predicates
    "EQUAL?": (2, None), "=?": (2, None), "==?": (2, None), "N=?": (2, None),
    "N==?": (2, None), "G?": (2, 2), "L?": (2, 2), "G=?": (2, 2), "L=?": (2, 2),
    "ZERO?": (1, 1), "0?": (1, 1), "1?": (1, 1), "FSET?": (2, 2), "IN?": (2, 2),
    "NOT": (1, 1), "AND": (1, None), "OR": (1, None), "VERIFY": (0, 0), "T?": (1, 1),
    # variables
    "SET": (2, 2), "SETG": (2, 2), "INC": (1, 1), "DEC": (1, 1),
    # objects
    "MOVE": (2, 2), "REMOVE": (1, 1), "FSET": (2, 2), "FCLEAR": (2, 2), "LOC": (1, 1),
    "FIRST?": (1, 1), "NEXT?": (1, 1), "GETP": (2, 2), "PUTP": (3, 3), "GETPT": (2, 2),
    "PTSIZE": (1, 1), "NEXTP": (2, 2),
    # tables
    "GET": (2, 2), "PUT": (3, 3), "GETB": (2, 2), "PUTB": (3, 3),
    # output
    "PRINT": (1, 1), "PRINTI": (1, 1), "PRINTN": (1, 1), "PRINTD": (1, 1),
    "PRINTC": (1, 1), "PRINTB": (1, 1), "CRLF": (0, 0),
    # input
    "READ": (1, 2), "LEX": (2, 2), "INPUT": (1, 1),
    # screen
    "SPLIT": (1, 1), "SCREEN": (1, 1), "CURSET": (2, 3), "HLIGHT": (1, 1),
    "CLEAR": (1, 1), "COLOR": (2, 3), "BUFOUT": (1, 1),
    # screen, version 6 only (§8.8): the compiler checks the target allows
    # them (driver.compatible_targets), the assembler that the opcode exists
    "WINGET": (2, 2), "WINPUT": (3, 3), "WINATTR": (2, 3), "WINSIZE": (3, 3),
    "WINPOS": (3, 3), "MARGIN": (2, 3), "SCROLL": (2, 2), "FONT": (1, 2),
    "MOUSE-LIMIT": (1, 1), "MOUSE-INFO": (1, 1), "MENU": (2, 2),
    "DISPLAY": (1, 3), "DCLEAR": (1, 3), "PICINF": (2, 2), "PICSET": (1, 1),
    "PRINTF": (1, 1), "BUFFER-SCREEN": (1, 1), "XPUSH": (2, 2), "POP": (1, 2),
    # control
    "RTRUE": (0, 0), "RFALSE": (0, 0), "RFATAL": (0, 0), "RETURN": (0, 1),
    "AGAIN": (0, 0), "APPLY": (1, 8), "QUIT": (0, 0), "RESTART": (0, 0),
    "SAVE": (0, 0), "RESTORE": (0, 0),
}
# forms whose FIRST argument is a variable NAME (a bare atom)
NAMES_A_VARIABLE = {"SET", "SETG", "INC", "DEC"}


@dataclass
class Symbols:
    """Symbol table: names and what they refer to (routines, globals, constants,
    objects, flags, properties) and dictionary words used in the program."""
    routines: dict = field(default_factory=dict)      # name -> RoutineDecl
    globals: dict = field(default_factory=dict)       # name -> GlobalDecl
    constants: dict = field(default_factory=dict)     # name -> ConstantDecl
    objects: dict = field(default_factory=dict)       # name -> (number, ObjectDecl)
    flags: dict = field(default_factory=dict)         # name -> attribute number
    properties: dict = field(default_factory=dict)    # name -> property number
    words: list = field(default_factory=list)         # dictionary words

    def kind_of(self, name: str) -> str | None:
        """What does ,NAME refer to?"""
        if name.startswith("P?") and name[2:] in self.properties:
            return "property"
        for kind, table in (("global", self.globals), ("constant", self.constants),
                            ("object", self.objects), ("routine", self.routines),
                            ("flag", self.flags)):
            if name in table:
                return kind
        return None

    def add_word(self, word: str) -> None:
        """Record a dictionary word W?word used in the program."""
        if word not in self.words:
            self.words.append(word)


class Analyser:
    """Build the symbol table and check that all names are defined and used correctly."""
    def __init__(self, program: ast.Program, diag: Diagnostics):
        self.p = program
        self.diag = diag
        self.s = Symbols()

    def error(self, node, message: str) -> None:
        """Report an error at a node's location."""
        self.diag.error(node.loc, message)

    # ---------------------------------------------------------- declarations
    def declare(self) -> None:
        seen: dict[str, str] = {}

        def unique(name: str, kind: str, node) -> bool:
            if name in seen:
                self.error(node, f"{name} is already defined as a {seen[name]}")
                return False
            seen[name] = kind
            return True

        for c in self.p.constants:
            if unique(c.name, "constant", c):
                self.s.constants[c.name] = c
        for g in self.p.globals:
            if unique(g.name, "global", g):
                self.s.globals[g.name] = g
        if len(self.s.globals) > 239:          # one global is kept for the compiler
            self.error(self.p.globals[239], "too many globals (239 maximum)")
        for r in self.p.routines:
            if unique(r.name, "routine", r):
                self.s.routines[r.name] = r
        for o in self.p.objects:
            if unique(o.name, "room" if o.is_room else "object", o):
                self.s.objects[o.name] = (len(self.s.objects) + 1, o)

        def add_property(name: str, node) -> None:
            if name not in self.s.properties:
                if len(self.s.properties) >= MAX_PROPERTIES:
                    self.error(node, "too many properties (63 maximum, §12.2)")
                    return
                self.s.properties[name] = len(self.s.properties) + 1

        for d in self.p.directions:
            add_property(d, self.p.objects[0] if self.p.objects else self.p.routines[0])
        for pd in self.p.propdefs:
            add_property(pd.name, pd)
        for o in self.p.objects:
            if o.synonyms:
                add_property("SYNONYM", o)
            if o.adjectives:
                add_property("ADJECTIVE", o)
            for name, value in o.properties:
                add_property(name, value)
            for flag, loc in o.flags:
                if flag not in self.s.flags:
                    if len(self.s.flags) >= MAX_ATTRIBUTES:
                        self.diag.error(loc, "too many FLAGS (48 attributes maximum, §12.3.1)")
                        continue
                    self.s.flags[flag] = len(self.s.flags)
            for w in o.synonyms + o.adjectives:
                self.s.add_word(w)
            if o.parent and o.parent not in {x.name for x in self.p.objects}:
                self.error(o, f"(IN {o.parent}): {o.parent} is not a defined object or room")

        if ENTRY_ROUTINE not in self.s.routines:
            loc = self.p.routines[0] if self.p.routines else None
            if loc:
                self.error(loc, f"no <ROUTINE {ENTRY_ROUTINE} ...>: every game starts at GO")

    # ------------------------------------------------------------- routines
    def check_routine(self, r: ast.RoutineDecl) -> None:
        """Check one routine: validate all expressions use defined names and that
        argument counts to built-ins and routines are correct. Track loop depth
        (for AGAIN) and local variable scope (for shadowing detection, ADR-017)."""
        self.routine = r
        self.locals = set(r.local_names())
        self.declared = set(r.local_names())   # written in the ROUTINE's argument list
        self.bound: list[str] = []             # names bound by enclosing PROG/BIND/DO/...
        self.loop_depth = 0

        # Check default values for optional and auxiliary arguments.
        for _name, default in r.optionals + r.auxes:
            if default is not None:
                self.expr(default)

        # Check every expression in the routine's body.
        for e in r.body:
            self.expr(e)

        # The Z-machine (§5.2) allows at most 15 local variables per routine.
        if len(r.local_names()) > MAX_LOCALS:
            self.error(r, f"{r.name} has {len(r.local_names())} locals; the Z-machine allows 15")

    def _auto_local(self, name: str) -> None:
        """DO / MAP-CONTENTS / REPEAT loop variables become AUX locals."""
        if name not in self.locals:
            self.routine.auxes.append((name, None))
            self.locals.add(name)

    def expr(self, e) -> None:
        """Recursively check an expression: verify all names are defined and validate
        argument counts to built-ins and user routines."""
        if isinstance(e, ast.Local):
            if e.name not in self.locals:
                hint = f"; {e.name} is a global, use ,{e.name}" if self.s.kind_of(e.name) else ""
                self.error(e, f"unknown local variable .{e.name}{hint}")
        elif isinstance(e, ast.Global):
            if self.s.kind_of(e.name) is None:
                self.error(e, f"unknown identifier ,{e.name}{self._hint(e.name)}")
        elif isinstance(e, ast.Word):
            self.s.add_word(e.word)
        elif isinstance(e, ast.Atom):
            self._bare_atom(e)
        elif isinstance(e, ast.Call):
            self.call(e)
        elif isinstance(e, ast.Cond):
            for test, body in e.clauses:
                if test is not None:
                    self.expr(test)
                for b in body:
                    self.expr(b)
        elif isinstance(e, ast.Repeat):
            for name, init in e.bindings:
                self._auto_local(name)
                if init is not None:
                    self.expr(init)
            self._loop(e.body)
        elif isinstance(e, ast.Do):
            self._auto_local(e.var)
            self.expr(e.start)
            self.expr(e.end)
            self._scoped([e.var], lambda: self._loop(e.body))
        elif isinstance(e, ast.MapContents):
            self._auto_local(e.var)
            self.expr(e.container)
            self._scoped([e.var], lambda: self._loop(e.body))
        elif isinstance(e, ast.Prog):
            self.prog(e)
        elif isinstance(e, ast.Tell):
            for item in e.items:
                if len(item) == 2 and not isinstance(item[1], str):
                    self.expr(item[1])
        elif isinstance(e, ast.Table):
            for item in e.items:
                self.expr(item)
        elif isinstance(e, ast.Zop):
            if e.opcode not in BY_NAME:
                self.error(e, f"ZOP: unknown opcode '{e.opcode}' (see §14)")
            for a in e.args:
                self.expr(a)

    def prog(self, e: ast.Prog) -> None:
        """PROG/BIND bindings are new variables for the block. A Z-machine
        routine has one fixed set of locals, so a binding becomes a hidden
        AUX local; sibling blocks may reuse a name, but re-binding a name
        that is still in use (shadowing) would clobber it - so it is an error."""
        names = []
        for name, init in e.bindings:
            if name in self.declared or name in self.bound:
                self.error(e, f"<{e.kind}> binds {name}, which is already a variable here; "
                              "rename it (shadowing is not supported, ADR-017)")
                continue
            if init is not None:
                self.expr(init)
            self._auto_local(name)
            names.append(name)
        if e.kind == "PROG":                   # RETURN/AGAIN target, like a loop
            self._scoped(names, lambda: self._loop(e.body))
        else:
            self._scoped(names, lambda: [self.expr(b) for b in e.body])

    def _scoped(self, names: list, walk) -> None:
        """Temporarily add names to self.bound (active scope) while walking the body."""
        self.bound += names
        walk()
        del self.bound[len(self.bound) - len(names):]

    def _hint(self, name: str) -> str:
        """Suggest how to fix an unknown identifier error."""
        if name in self.locals:
            return f"; {name} is a local, use .{name}"
        if name in ("PRSA", "PRSO", "PRSI"):
            return " (VERB?/PRSO?/PRSI? need the parser library: <INSERT-FILE \"lib/parser\">)"
        if name.startswith("V?"):
            return f" (no SYNTAX line has the action V-{name[2:]})"
        return ""

    def _loop(self, body: list) -> None:
        """Check a loop body (REPEAT, DO, MAP-CONTENTS, or PROG): AGAIN is only valid here."""
        self.loop_depth += 1
        for b in body:
            self.expr(b)
        self.loop_depth -= 1

    def _bare_atom(self, e: ast.Atom) -> None:
        """Bare atoms (T is allowed). Anything else should use . or , prefix."""
        if e.name == "T":
            return
        if e.name in self.locals:
            self.error(e, f"bare atom {e.name}: to use the local's value write .{e.name}")
        elif self.s.kind_of(e.name):
            self.error(e, f"bare atom {e.name}: to use its value write ,{e.name}")
        else:
            self.error(e, f"unknown identifier {e.name}")

    def call(self, e: ast.Call) -> None:
        """Check a function call or built-in: validate argument count, check for
        AGAIN outside loops, and validate SET/INC/DEC variable names."""
        args = e.args
        if e.name in BUILTINS:
            lo, hi = BUILTINS[e.name]
            if len(args) < lo or (hi is not None and len(args) > hi):
                expected = f"{lo}" if lo == hi else f"{lo} to {hi}" if hi else f"at least {lo}"
                self.error(e, f"<{e.name}> takes {expected} argument(s), got {len(args)}")
            if e.name in ("AGAIN",) and self.loop_depth == 0:
                self.error(e, "AGAIN is only allowed inside PROG / REPEAT / DO / MAP-CONTENTS")
            if e.name in NAMES_A_VARIABLE and args:
                self._variable_name(e, args[0])
                args = args[1:]
        elif e.name in self.s.routines:
            r = self.s.routines[e.name]
            lo, hi = len(r.params), len(r.params) + len(r.optionals)
            if not lo <= len(args) <= hi:
                expected = f"{lo}" if lo == hi else f"{lo} to {hi}"
                self.error(e, f"routine {e.name} takes {expected} argument(s), got {len(args)}")
            if len(args) > 7:
                self.error(e, "a routine call can pass at most 7 arguments (§15 call_vs2)")
        else:
            self.error(e, f"unknown routine or form <{e.name} ...>")
        for a in args:
            self.expr(a)

    def _variable_name(self, e: ast.Call, target) -> None:
        """SET X / SETG X / INC X take the variable's NAME (a bare atom)."""
        if isinstance(target, (ast.Local, ast.Global)):
            name = target.name   # ZILF also accepts <SET .X ...>; we allow it
        elif isinstance(target, ast.Atom):
            name = target.name
        else:
            self.error(e, f"<{e.name}> needs a variable name first")
            return
        if name in self.locals:
            return
        if name in self.s.globals:
            return
        self.error(target, f"<{e.name}>: {name} is not a local or global variable")

    def run(self) -> Symbols:
        """Build the symbol table: declare all names, check routines, then check
        global initializers and object properties for valid references."""
        # Declare all top-level names.
        self.declare()

        # Check each routine's body for valid names and argument counts.
        for r in self.p.routines:
            self.check_routine(r)

        # Check global initializers (outside any routine scope).
        for g in self.p.globals:
            self.routine, self.locals, self.loop_depth = None, set(), 0
            self.declared, self.bound = set(), []
            self.expr(g.init)

        # Check object properties: exits must point to defined rooms/objects.
        for o in self.p.objects:
            self.locals, self.loop_depth = set(), 0
            for _name, value in o.properties:
                if value.kind == "to":
                    if value.values[0] not in self.s.objects:
                        self.error(value, f"TO {value.values[0]}: not a defined room/object")
                else:
                    for v in value.values:
                        self.expr(v)
        return self.s


def analyse(program: ast.Program, diag: Diagnostics) -> Symbols:
    """Run semantic analysis: build the symbol table and check all names."""
    return Analyser(program, diag).run()
