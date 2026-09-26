"""Stage 3 - forms -> typed AST.

The reader gave us generic Forms and Lists. Here we decide what each form
MEANS. Top-level forms are declarations; forms inside a routine are
expressions. Only forms with unusual SYNTAX (COND's clause lists, TELL's
tokens, ROUTINE's argument list, ...) get their own parser function;
everything else becomes a generic ast.Call.
"""
from __future__ import annotations

from pathlib import Path

from zforge.compiler import ast
from zforge.compiler import reader as r
from zforge.compiler.diagnostics import Diagnostics
from zforge.compiler.grammar import OPTION_BITS

# <VERSION ...> names the version a source is WRITTEN for. EZIP is kept as
# 5 for v1 compatibility (ZILF uses ZIP=3, EZIP=4, XZIP=5, YZIP=6).
# --target may still pick a version with the same opcode set (driver.py).
SUPPORTED_VERSIONS = {"5": 5, "EZIP": 5, "XZIP": 5, "7": 7, "8": 8}


class FormParser:
    def __init__(self, diag: Diagnostics, base_dir: Path | None = None):
        self.diag = diag
        self.base_dir = base_dir or Path(".")
        self.program = ast.Program()

    def error(self, node, message: str) -> None:
        self.diag.error(node.location, message)

    # =============================================================== top level
    def parse_program(self, data: list) -> ast.Program:
        for datum in data:
            self.top_level(datum)
        return self.program

    def top_level(self, datum) -> None:
        if not isinstance(datum, r.Form) or not datum.items:
            if isinstance(datum, r.String):
                return                     # a bare string at top level is a comment
            self.error(datum, "expected a declaration such as <ROUTINE ...> or <GLOBAL ...>")
            return
        head, args = datum.items[0], datum.items[1:]
        name = head.name if isinstance(head, r.Atom) else ""
        handler = {
            "VERSION": self.version, "CONSTANT": self.constant, "GLOBAL": self.global_,
            "OBJECT": self.object, "ROOM": self.object, "ROUTINE": self.routine,
            "PROPDEF": self.propdef, "DIRECTIONS": self.directions,
            "INSERT-FILE": self.insert_file, "SYNTAX": self.syntax,
            "VERB-SYNONYM": self.synonym, "PREP-SYNONYM": self.synonym,
        }.get(name)
        if handler is None:
            self.error(head if hasattr(head, "location") else datum,
                       f"unsupported top-level form <{name or '?'} ...> (see docs/ZIL_SUBSET.md)")
            return
        handler(datum, args)

    def version(self, form, args) -> None:
        key = str(args[0].value) if args and isinstance(args[0], r.Number) else \
            (args[0].name if args and isinstance(args[0], r.Atom) else "")
        if key not in SUPPORTED_VERSIONS:
            self.error(form, f"only <VERSION 5> (EZIP/XZIP), <VERSION 7> or <VERSION 8> "
                             f"is supported, not {key or '?'}")
            return
        self.program.version = SUPPORTED_VERSIONS[key]

    def _name(self, form, args, what: str) -> str | None:
        if not args or not isinstance(args[0], r.Atom):
            self.error(form, f"{what} needs a name")
            return None
        return args[0].name

    def constant(self, form, args) -> None:
        name = self._name(form, args, "CONSTANT")
        if name and len(args) == 2:
            self.program.constants.append(ast.ConstantDecl(name, self.expr(args[1]), form.location))
        elif name:
            self.error(form, "CONSTANT takes a name and one value")

    def global_(self, form, args) -> None:
        name = self._name(form, args, "GLOBAL")
        if name:
            init = self.expr(args[1]) if len(args) > 1 else ast.Num(0, form.location)
            self.program.globals.append(ast.GlobalDecl(name, init, form.location))

    def propdef(self, form, args) -> None:
        name = self._name(form, args, "PROPDEF")
        if name:
            default = self.expr(args[1]) if len(args) > 1 else ast.Num(0, form.location)
            self.program.propdefs.append(ast.PropDefDecl(name, default, form.location))

    def directions(self, form, args) -> None:
        for a in args:
            if isinstance(a, r.Atom):
                self.program.directions.append(a.name)
            else:
                self.error(a, "DIRECTIONS takes atoms, e.g. <DIRECTIONS NORTH SOUTH>")

    def insert_file(self, form, args) -> None:
        """<INSERT-FILE "name">: textually include name.zil (same directory)."""
        from zforge.compiler.driver import read_source   # avoid an import cycle
        if not args or not isinstance(args[0], r.String):
            self.error(form, 'INSERT-FILE needs a "file name"')
            return
        path = self.base_dir / args[0].value
        if path.suffix == "":
            path = path.with_suffix(".zil")
        if not path.exists():
            self.error(form, f"INSERT-FILE: {path} not found")
            return
        for datum in read_source(path.read_text(), self.diag):
            self.top_level(datum)

    # ------------------------------------------------------------- grammar
    def syntax(self, form, args) -> None:
        """<SYNTAX TAKE OBJECT (FIND TAKEBIT) = V-TAKE PRE-TAKE>

        After the verb: prepositions (any atom) and up to two OBJECT slots,
        then '=' and the action routine, optionally a preaction routine.
        A preposition goes with the OBJECT that follows it; one after the
        last OBJECT is a trailing particle (TURN OBJECT OFF)."""
        if not args or not isinstance(args[0], r.Atom):
            self.error(form, "SYNTAX needs a verb, e.g. <SYNTAX TAKE OBJECT = V-TAKE>")
            return
        verb, objects, preps, finds = args[0].name, 0, [None, None], [None, None]
        options: list[set] = [set(), set()]
        rest = list(args[1:])
        while rest and not (isinstance(rest[0], r.Atom) and rest[0].name == "="):
            item = rest.pop(0)
            if isinstance(item, r.Atom) and item.name == "OBJECT":
                if objects == 2:
                    self.error(item, "SYNTAX allows at most two OBJECTs")
                objects = min(objects + 1, 2)
            elif isinstance(item, r.List):
                if objects == 0:
                    self.error(item, "an (option list) must follow an OBJECT")
                else:
                    finds[objects - 1] = self._syntax_options(item, finds[objects - 1],
                                                              options[objects - 1])
            elif isinstance(item, r.Atom):
                slot = min(objects, 1)
                if preps[slot] is not None or objects == 2:
                    self.error(item, f"unexpected preposition {item.name}: one per OBJECT "
                                     "(plus one trailing particle)")
                else:
                    preps[slot] = item.name.lower()
            else:
                self.error(item, "SYNTAX patterns contain only words, OBJECT and (options)")
        if not rest:
            self.error(form, "SYNTAX needs '= ACTION-ROUTINE' at the end")
            return
        routines = rest[1:]
        if not routines or len(routines) > 2 or not all(isinstance(x, r.Atom) for x in routines):
            self.error(rest[0], "after '=' give the action routine and optionally a preaction")
            return
        self.program.syntaxes.append(ast.SyntaxDecl(
            verb.lower(), objects, preps, finds, routines[0].name,
            routines[1].name if len(routines) == 2 else None, form.location, options))

    # search options ZIL writes after OBJECT. The parser library uses the
    # ones in grammar.OPTION_BITS to PREFER candidates (ADR-019); the rest
    # are accepted so that real ZIL grammar compiles, and ignored.
    IGNORED_SEARCH_OPTIONS = {"TAKE", "MANY", "EVERYWHERE", "SEARCH", "ADJACENT"}

    def _syntax_options(self, lst, find, options: set):
        items = lst.items
        if items and isinstance(items[0], r.Atom) and items[0].name == "FIND":
            if len(items) != 2 or not isinstance(items[1], r.Atom):
                self.error(lst, "write (FIND FLAGNAME)")
                return find
            return items[1].name
        for item in items:
            name = item.name if isinstance(item, r.Atom) else None
            if name in OPTION_BITS:
                options.add(name)
            elif name not in self.IGNORED_SEARCH_OPTIONS:
                self.error(item, "unsupported SYNTAX option (use (FIND flag), HELD CARRIED "
                                 "HAVE ON-GROUND IN-ROOM INSIDE-PRSI, or TAKE MANY ...)")
        return find

    def synonym(self, form, args) -> None:
        """<VERB-SYNONYM TAKE GET GRAB> / <PREP-SYNONYM IN INTO INSIDE>"""
        kind = form.items[0].name.split("-")[0]
        if len(args) < 2 or not all(isinstance(a, r.Atom) for a in args):
            self.error(form, f"{kind}-SYNONYM needs a word and at least one synonym")
            return
        self.program.synonyms.append(ast.SynonymDecl(
            kind, args[0].name.lower(), [a.name.lower() for a in args[1:]], form.location))

    # ------------------------------------------------------------- objects
    def object(self, form, args) -> None:
        name = self._name(form, args, "OBJECT")
        if not name:
            return
        is_room = form.items[0].name == "ROOM"
        obj = ast.ObjectDecl(name, is_room, form.location)
        for clause in args[1:]:
            if not isinstance(clause, r.List) or not clause.items or \
                    not isinstance(clause.items[0], r.Atom):
                self.error(clause, "object properties look like (NAME values...)")
                continue
            key, values = clause.items[0].name, clause.items[1:]
            if key in ("IN", "LOC"):
                if len(values) == 1 and isinstance(values[0], r.Atom):
                    obj.parent = values[0].name
                else:
                    self.error(clause, f"({key} ...) takes one object name")
            elif key == "DESC":
                if len(values) == 1 and isinstance(values[0], r.String):
                    obj.desc = values[0].value
                else:
                    self.error(clause, '(DESC "...") takes one string')
            elif key == "FLAGS":
                obj.flags += [(v.name, v.location) for v in values if isinstance(v, r.Atom)]
            elif key in ("SYNONYM", "ADJECTIVE"):
                words = [v.name.lower() for v in values if isinstance(v, r.Atom)]
                (obj.synonyms if key == "SYNONYM" else obj.adjectives).extend(words)
            elif values and isinstance(values[0], r.Atom) and values[0].name == "TO":
                if len(values) == 2 and isinstance(values[1], r.Atom):
                    obj.properties.append((key, ast.PropValue("to", [values[1].name],
                                                              clause.location)))
                else:
                    self.error(clause, f"({key} TO room) needs one room name")
            else:
                if not values:
                    self.error(clause, f"property ({key}) needs at least one value")
                    continue
                exprs = [self._prop_value(v) for v in values]
                obj.properties.append((key, ast.PropValue("words", exprs, clause.location)))
        self.program.objects.append(obj)

    def _prop_value(self, v):
        """Inside property lists a bare atom names an object or routine."""
        if isinstance(v, r.Atom):
            return ast.Global(v.name, v.location)
        return self.expr(v)

    # ------------------------------------------------------------ routines
    def routine(self, form, args) -> None:
        name = self._name(form, args, "ROUTINE")
        if not name:
            return
        if len(args) < 2 or not isinstance(args[1], r.List):
            self.error(form, "ROUTINE needs an argument list, e.g. <ROUTINE GO () ...>")
            return
        params, optionals, auxes = [], [], []
        section = "required"
        for item in args[1].items:
            if isinstance(item, r.String):
                marker = item.value.upper()
                if marker in ("OPT", "OPTIONAL"):
                    section = "opt"
                elif marker in ("AUX", "EXTRA"):
                    section = "aux"
                else:
                    self.error(item, f'unknown argument marker "{item.value}" (use "OPT" or "AUX")')
                continue
            if isinstance(item, r.Atom):
                entry, default = item.name, None
            elif isinstance(item, r.List) and len(item.items) == 2 and \
                    isinstance(item.items[0], r.Atom):
                entry, default = item.items[0].name, self.expr(item.items[1])
            else:
                self.error(item, "arguments are NAME or (NAME default)")
                continue
            if section == "required":
                if default is not None:
                    self.error(item, 'a default needs "OPT" or "AUX" before it')
                params.append(entry)
            elif section == "opt":
                optionals.append((entry, default))
            else:
                auxes.append((entry, default))
        body = [self.expr(e) for e in args[2:]]
        self.program.routines.append(ast.RoutineDecl(name, params, optionals, auxes, body,
                                                     form.location))

    # ========================================================= expressions
    def expr(self, d):
        if isinstance(d, r.Number):
            return ast.Num(d.value, d.location)
        if isinstance(d, r.String):
            return ast.Str(d.value, d.location)
        if isinstance(d, r.LocalRef):
            return ast.Local(d.name, d.location)
        if isinstance(d, r.GlobalRef):
            if d.name.startswith("W?"):
                return ast.Word(d.name[2:].lower(), d.location)
            return ast.Global(d.name, d.location)
        if isinstance(d, r.Atom):
            if d.name.startswith("W?"):
                return ast.Word(d.name[2:].lower(), d.location)
            return ast.Atom(d.name, d.location)
        if isinstance(d, r.List):
            self.error(d, "a (list) is not an expression here")
            return ast.False_(d.location)
        # a Form
        if not d.items:
            return ast.False_(d.location)
        head = d.items[0]
        if not isinstance(head, r.Atom):
            self.error(d, "a form must start with a name, e.g. <PRINTN .X>")
            return ast.False_(d.location)
        special = {
            "COND": self.cond, "REPEAT": self.repeat, "DO": self.do,
            "MAP-CONTENTS": self.map_contents, "TELL": self.tell,
            "TABLE": self.table, "LTABLE": self.table, "PTABLE": self.table,
            "ITABLE": self.table, "ZOP": self.zop,
            "PROG": self.prog, "BIND": self.prog,
            "VERB?": self.verb_p, "PRSO?": self.prs_p, "PRSI?": self.prs_p,
        }.get(head.name)
        if special:
            return special(d, d.items[1:])
        return ast.Call(head.name, [self.expr(a) for a in d.items[1:]], d.location)

    def cond(self, form, args):
        clauses = []
        for clause in args:
            if not isinstance(clause, r.List) or not clause.items:
                self.error(clause, "COND clauses look like (test body...)")
                continue
            test = clause.items[0]
            if isinstance(test, r.Atom) and test.name in ("ELSE", "T"):
                test_expr = None
            else:
                test_expr = self.expr(test)
            clauses.append((test_expr, [self.expr(e) for e in clause.items[1:]]))
        return ast.Cond(clauses, form.location)

    def _bindings(self, lst) -> list:
        out = []
        for item in lst.items:
            if isinstance(item, r.Atom):
                out.append((item.name, None))
            elif isinstance(item, r.List) and len(item.items) == 1 and \
                    isinstance(item.items[0], r.Atom):
                out.append((item.items[0].name, None))       # (X) = X, no initial value
            elif isinstance(item, r.List) and len(item.items) == 2 and \
                    isinstance(item.items[0], r.Atom):
                out.append((item.items[0].name, self.expr(item.items[1])))
            else:
                self.error(item, "bindings are NAME, (NAME) or (NAME value)")
        return out

    def repeat(self, form, args):
        if not args or not isinstance(args[0], r.List):
            self.error(form, "REPEAT needs a binding list first, e.g. <REPEAT () ...>")
            return ast.False_(form.location)
        return ast.Repeat(self._bindings(args[0]), [self.expr(e) for e in args[1:]],
                          form.location)

    def prog(self, form, args):
        """<PROG (bindings) body...> / <BIND (bindings) body...>"""
        kind = form.items[0].name
        if not args or not isinstance(args[0], r.List):
            self.error(form, f"{kind} needs a binding list first, e.g. <{kind} ((X 1)) ...>")
            return ast.False_(form.location)
        return ast.Prog(kind, self._bindings(args[0]), [self.expr(e) for e in args[1:]],
                        form.location)

    def verb_p(self, form, args):
        """<VERB? TAKE DROP>  ==  <EQUAL? ,PRSA ,V?TAKE ,V?DROP>"""
        if not args or not all(isinstance(a, r.Atom) for a in args):
            self.error(form, "VERB? takes action names, e.g. <VERB? TAKE DROP>")
            return ast.False_(form.location)
        loc = form.location
        return ast.Call("EQUAL?", [ast.Global("PRSA", loc)] +
                        [ast.Global("V?" + a.name, a.location) for a in args], loc)

    def prs_p(self, form, args):
        """<PRSO? LAMP CLOAK>  ==  <EQUAL? ,PRSO ,LAMP ,CLOAK>  (same for PRSI?)"""
        if not args:
            self.error(form, f"{form.items[0].name} needs at least one object")
            return ast.False_(form.location)
        var = form.items[0].name[:-1]              # PRSO? -> PRSO
        objs = [ast.Global(a.name, a.location) if isinstance(a, r.Atom) else self.expr(a)
                for a in args]
        return ast.Call("EQUAL?", [ast.Global(var, form.location)] + objs, form.location)

    def do(self, form, args):
        spec = args[0] if args else None
        if not isinstance(spec, r.List) or len(spec.items) not in (3, 4) or \
                not isinstance(spec.items[0], r.Atom):
            self.error(form, "DO looks like <DO (I start end [step]) body...>")
            return ast.False_(form.location)
        step = 1
        if len(spec.items) == 4:
            if isinstance(spec.items[3], r.Number) and spec.items[3].value != 0:
                step = spec.items[3].value
            else:
                self.error(spec.items[3], "DO step must be a non-zero number")
        return ast.Do(spec.items[0].name, self.expr(spec.items[1]), self.expr(spec.items[2]),
                      step, [self.expr(e) for e in args[1:]], form.location)

    def map_contents(self, form, args):
        spec = args[0] if args else None
        if not isinstance(spec, r.List) or len(spec.items) != 2 or \
                not isinstance(spec.items[0], r.Atom):
            self.error(form, "MAP-CONTENTS looks like <MAP-CONTENTS (I ,CONTAINER) body...>")
            return ast.False_(form.location)
        return ast.MapContents(spec.items[0].name, self.expr(spec.items[1]),
                               [self.expr(e) for e in args[1:]], form.location)

    def tell(self, form, args):
        """TELL tokens: "string"  CR/CRLF  N x  D x  C x  or any value
        (printed as a packed string address)."""
        items, i = [], 0
        while i < len(args):
            a = args[i]
            if isinstance(a, r.String):
                items.append(("str", a.value))
            elif isinstance(a, r.Atom) and a.name in ("CR", "CRLF"):
                items.append(("cr",))
            elif isinstance(a, r.Atom) and a.name in ("N", "D", "C", "B"):
                if i + 1 >= len(args):
                    self.error(a, f"TELL {a.name} needs a value after it")
                    break
                kind = {"N": "num", "D": "obj", "C": "char", "B": "addr"}[a.name]
                items.append((kind, self.expr(args[i + 1])))
                i += 1
            else:
                items.append(("paddr", self.expr(a)))
            i += 1
        return ast.Tell(items, form.location)

    def table(self, form, args):
        kind = form.items[0].name
        kind = "TABLE" if kind == "PTABLE" else kind
        byte = False
        items = []
        for a in args:
            if isinstance(a, r.List):          # flags such as (BYTE) (PURE)
                for flag in a.items:
                    if isinstance(flag, r.Atom) and flag.name == "BYTE":
                        byte = True
                continue
            if kind == "ITABLE" and isinstance(a, r.Atom) and a.name in ("BYTE", "WORD"):
                byte = a.name == "BYTE"
                continue
            items.append(self.expr(a))
        if kind == "ITABLE" and not 1 <= len(items) <= 2:
            self.error(form, "ITABLE looks like <ITABLE count [initial value]>")
        return ast.Table(kind, byte, items, form.location)

    def zop(self, form, args):
        if not args or not isinstance(args[0], r.Atom):
            self.error(form, "ZOP needs an opcode name, e.g. <ZOP PRINT_UNICODE 65>")
            return ast.False_(form.location)
        return ast.Zop(args[0].name.lower().replace("-", "_"),
                       [self.expr(a) for a in args[1:]], form.location)
