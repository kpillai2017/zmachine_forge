"""The assembler: .zas text -> a story file (version 5 by default).

Every version-dependent choice (packed addresses, alignment, header
version byte, file-length divisor) comes from a VersionProfile
(common/versions.py).

Passes:
  1. collect   - read directives: globals, constants, objects, arrays,
                 strings, dictionary words, routines (with their bodies)
  2. size      - turn each instruction into an Encoded record whose SIZE
                 is known; branch offsets start short (1 byte) and are
                 widened until every branch fits ("relaxation", §4.7)
  3. layout    - give every table, routine and string an address
                 (see linker.py for the memory map)
  4. emit      - resolve symbols to numbers and write the bytes

Operand sizes never depend on addresses: anything that is an ADDRESS
(routine, string, array, dictionary word) is always a 2-byte constant.
That keeps pass 2 independent of pass 3.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from zforge.asm import linker
from zforge.asm.linker import ObjectDef, align
from zforge.asm.syntax import AsmError, AsmInstruction, Directive, Label, parse, unquote
from zforge.common import header as H
from zforge.common.opcodes import DOUBLE_TYPE_BYTE, Op, names_for
from zforge.common.text import encode_string
from zforge.common.versions import DEFAULT_VERSION, profile_for
from zforge.vm.decoder import OperandType

# Opcodes whose first operand is a variable NUMBER (§6.3.4 indirect reference)
INDIRECT_FIRST = {"inc", "dec", "inc_chk", "dec_chk", "load", "store", "pull"}
NUMBER_RE = re.compile(r"^-?(\d+|\$[0-9a-fA-F]+|0x[0-9a-fA-F]+)$")


def parse_number(token: str) -> int | None:
    if not NUMBER_RE.match(token):
        return None
    sign = -1 if token.startswith("-") else 1
    t = token.lstrip("-")
    if t.startswith("$"):
        return sign * int(t[1:], 16)
    return sign * int(t, 0)


@dataclass
class RoutineDef:
    name: str
    locals: list[str]
    body: list = field(default_factory=list)      # AsmInstruction | Label
    line: int = 0


@dataclass
class Encoded:
    """One instruction ready to be sized and emitted."""
    op: Op
    operands: list[tuple[OperandType, object]]   # (type, int | callable)
    store: int | None
    branch: tuple[bool, str] | None              # (on_true, label/"rtrue"/"rfalse")
    text: bytes | None
    long_branch: bool = False
    line: int = 0
    offset: int = 0                              # from the routine's first instruction

    def form(self) -> str:
        if self.op.kind == "EXT":
            return "extended"
        if self.op.kind == "2OP" and len(self.operands) == 2 and \
                all(t != OperandType.LARGE for t, _ in self.operands):
            return "long"
        if self.op.kind in ("1OP", "0OP"):
            return "short"
        return "variable"

    def size(self) -> int:
        form = self.form()
        n = {"long": 1, "short": 1, "variable": 2, "extended": 3}[form]
        if self.op.name in DOUBLE_TYPE_BYTE:
            n += 1
        n += sum(2 if t == OperandType.LARGE else 1 for t, _ in self.operands)
        n += 1 if self.store is not None else 0
        if self.branch is not None:
            n += 2 if self.long_branch else 1
        n += len(self.text) if self.text else 0
        return n


@dataclass
class Layout:
    """Where each part of the story file was placed (filled by pass 3)."""
    abbreviations: int = 0
    object_table: int = 0
    globals_table: int = 0
    static_memory: int = 0
    high_memory: int = 0
    stub: int = 0
    prop_addresses: list = field(default_factory=list)
    routine_places: list = field(default_factory=list)
    string_places: list = field(default_factory=list)


class Assembler:
    def __init__(self, source: str = "<zas>", version: int = DEFAULT_VERSION):
        self.source = source
        self.profile = profile_for(version)                # §1.2.3, §11.1.6, ...
        self.opcodes = names_for(version)                  # §14: this version's set
        # §1.2.3: in v6/v7 a packed address P means 4P + 8*R_O (routines) or
        # 4P + 8*S_O (strings). _start_area() chooses them; 0 elsewhere.
        self.routines_offset = 0
        self.strings_offset = 0
        self.release, self.serial = 1, "000000"
        self.globals: dict[str, tuple[int, str]] = {}      # name -> (var number, init)
        self.constants: dict[str, int] = {}
        self.arrays: dict[str, tuple[str, list[str]]] = {}  # name -> (kind, tokens)
        self.objects: list[ObjectDef] = []
        self.object_numbers: dict[str, int] = {}
        self.prop_defaults: dict[int, str] = {}
        self.words: list[str] = []
        self.separators = '.,"'
        self.strings: dict[str, str] = {}                  # name -> text
        self.routines: list[RoutineDef] = []
        self.main = "main"
        self.want_undo = False
        self.addresses: dict[str, int] = {}                # filled by layout

    def error(self, message: str, line: int) -> AsmError:
        return AsmError(message, line, self.source)

    # ================================================================ pass 1
    def collect(self, text: str) -> None:
        current: RoutineDef | None = None
        for item in parse(text, self.source).items:
            if isinstance(item, Directive) and item.name in (".routine", ".end"):
                if item.name == ".routine":
                    if current:
                        raise self.error("nested .routine (missing .end?)", item.line)
                    if not item.args:
                        raise self.error(".routine needs a name", item.line)
                    current = RoutineDef(item.args[0], item.args[1:], line=item.line)
                    if len(current.locals) > 15:
                        raise self.error("a routine may have at most 15 locals", item.line)
                else:
                    if not current:
                        raise self.error(".end without .routine", item.line)
                    self.routines.append(current)
                    current = None
            elif current is not None:
                if isinstance(item, Directive):
                    raise self.error(f"{item.name} not allowed inside a routine", item.line)
                current.body.append(item)
                if isinstance(item, AsmInstruction) and item.opcode == "save_undo":
                    self.want_undo = True
            elif isinstance(item, Directive):
                self._directive(item)
            else:
                raise self.error("instruction outside a .routine", item.line)
        if current:
            raise self.error(f"routine {current.name} has no .end", current.line)

    def _check_new_name(self, name: str, line: int) -> None:
        """A second definition must be an error: silently keeping one of
        them turns a naming slip into a wrong address at run time."""
        if name in self.globals or name in self.constants or name in self.arrays:
            raise self.error(f"{name} is defined twice", line)

    def _directive(self, d: Directive) -> None:
        a = d.args
        need = {".global": 1, ".constant": 2, ".array": 2, ".buffer": 2, ".object": 2,
                ".prop": 3, ".propb": 3, ".propdefault": 2, ".string": 2, ".main": 1}
        if len(a) < need.get(d.name, 0):
            raise self.error(f"{d.name} needs at least {need[d.name]} arguments", d.line)
        if d.name in (".global", ".constant", ".array", ".buffer"):
            self._check_new_name(a[0], d.line)
        if d.name == ".release":
            self.release = parse_number(a[0]) or 0
        elif d.name == ".serial":
            self.serial = unquote(a[0]) if a[0].startswith('"') else a[0]
        elif d.name == ".global":
            if len(self.globals) >= linker.GLOBAL_COUNT:
                raise self.error("too many globals (240 maximum)", d.line)
            self.globals[a[0]] = (16 + len(self.globals), a[1] if len(a) > 1 else "0")
        elif d.name == ".constant":
            self.constants[a[0]] = self._constant_value(a[1], d.line)
        elif d.name == ".array":
            if a[1] not in ("word", "byte"):
                raise self.error(".array kind must be word or byte", d.line)
            self.arrays[a[0]] = (a[1], a[2:])
        elif d.name == ".buffer":
            self.arrays[a[0]] = ("byte", ["0"] * self._constant_value(a[1], d.line))
        elif d.name == ".object":
            obj = ObjectDef(a[0], unquote(a[1]) if a[1].startswith('"') else a[1], "0", line=d.line)
            for extra in a[2:]:
                key, _, value = extra.partition("=")
                if key == "parent":
                    obj.parent = value
                elif key == "attrs":
                    obj.attributes = [self._constant_value(v, d.line)
                                      for v in value.split(",") if v]
                else:
                    raise self.error(f"unknown .object option {extra}", d.line)
            self.object_numbers[obj.name] = len(self.objects) + 1
            self.objects.append(obj)
        elif d.name in (".prop", ".propb"):
            obj = self._object(a[0], d.line)
            number = self._constant_value(a[1], d.line)
            if not 1 <= number <= 63:
                raise self.error("property numbers are 1..63 (§12.2)", d.line)
            obj.properties[number] = ("word" if d.name == ".prop" else "byte", a[2:])
        elif d.name == ".propdefault":
            self.prop_defaults[self._constant_value(a[0], d.line)] = a[1]
        elif d.name == ".dict":
            self.words += [unquote(w) for w in a]
        elif d.name == ".separators":
            self.separators = unquote(a[0]) if a else ""
        elif d.name == ".string":
            self.strings[a[0]] = unquote(a[1])
        elif d.name == ".main":
            self.main = a[0]
        elif d.name == ".undo":
            self.want_undo = True

    def _object(self, name: str, line: int) -> ObjectDef:
        if name not in self.object_numbers:
            raise self.error(f"unknown object {name} (define it with .object first)", line)
        return self.objects[self.object_numbers[name] - 1]

    def _constant_value(self, token: str, line: int) -> int:
        n = parse_number(token)
        if n is not None:
            return n
        if token in self.constants:
            return self.constants[token]
        if token in self.object_numbers:
            return self.object_numbers[token]
        raise self.error(f"{token} is not a number or a known constant", line)

    # ================================================== operands & variables
    def variable_number(self, token: str, routine: RoutineDef | None) -> int | None:
        if token == "sp":
            return 0
        if routine and token in routine.locals:
            return routine.locals.index(token) + 1
        m = re.fullmatch(r"L(\d\d)", token)
        if m and int(m.group(1)) < 15:
            return int(m.group(1)) + 1
        m = re.fullmatch(r"G([0-9a-fA-F]{2})", token)
        if m and int(m.group(1), 16) < 240:
            return int(m.group(1), 16) + 16
        if token in self.globals:
            return self.globals[token][0]
        return None

    def operand(self, token: str, routine: RoutineDef | None, line: int):
        """Classify one operand -> (OperandType, value or late resolver)."""
        var = self.variable_number(token, routine)
        if var is not None:
            return OperandType.VARIABLE, var
        n = parse_number(token)
        if n is None and token in self.constants:
            n = self.constants[token]
        if n is None and token in self.object_numbers:
            n = self.object_numbers[token]
        if n is not None:
            n &= 0xFFFF
            return (OperandType.SMALL if n <= 255 else OperandType.LARGE), n
        if token.startswith('"'):
            name = self.intern_string(unquote(token))
            return OperandType.LARGE, lambda: self.packed(name, line)
        if token.startswith("'"):
            word = unquote(token).lower()
            if word not in self.words:
                self.words.append(word)
            return OperandType.LARGE, lambda: self.dict_address(word, line)
        return OperandType.LARGE, lambda: self.resolve_symbol(token, line)

    def intern_string(self, text: str) -> str:
        for name, existing in self.strings.items():
            if existing == text:
                return name
        name = f"__str{len(self.strings)}"
        self.strings[name] = text
        return name

    # ============================================================== pass 2
    def encode_routine(self, routine: RoutineDef) -> tuple[list, dict[str, int]]:
        encoded: list = []
        for item in routine.body:
            if isinstance(item, Label):
                encoded.append(item)
                continue
            encoded.append(self.encode_instruction(item, routine))
        return encoded, self.relax(encoded, routine)

    def encode_instruction(self, ins: AsmInstruction, routine: RoutineDef) -> Encoded:
        op = self.opcodes.get(ins.opcode)
        if op is None:
            raise self.error(f"unknown opcode '{ins.opcode}' (see §14)", ins.line)
        operands = []
        text = None
        tokens = list(ins.operands)
        if op.text:
            if len(tokens) != 1 or not tokens[0].startswith('"'):
                raise self.error(f"{op.name} needs exactly one \"string\"", ins.line)
            text = encode_string(unquote(tokens[0]))
            tokens = []
        if op.name == "jump":
            if len(tokens) != 1:
                raise self.error("jump needs a label", ins.line)
            return Encoded(op, [(OperandType.LARGE, ("jump", tokens[0]))], None, None, None,
                           line=ins.line)
        for i, token in enumerate(tokens):
            if i == 0 and op.name in INDIRECT_FIRST:
                if token.startswith("[") and token.endswith("]"):
                    operands.append(self.operand(token[1:-1], routine, ins.line))
                    continue
                var = self.variable_number(token, routine)
                if var is not None:          # pass the variable NUMBER as a constant
                    operands.append((OperandType.SMALL, var))
                    continue
            operands.append(self.operand(token, routine, ins.line))
        store = None
        if op.store:
            if ins.store is None:
                raise self.error(f"{op.name} stores a result: add '-> variable'", ins.line)
            store = self.variable_number(ins.store, routine)
            if store is None:
                raise self.error(f"'{ins.store}' is not a variable", ins.line)
        elif ins.store is not None:
            raise self.error(f"{op.name} does not store a result", ins.line)
        branch = None
        if op.branch:
            if ins.branch is None:
                raise self.error(f"{op.name} is a branch instruction: add '?label'", ins.line)
            on_true = not ins.branch.startswith("?~")
            branch = (on_true, ins.branch[2:] if not on_true else ins.branch[1:])
        elif ins.branch is not None:
            raise self.error(f"{op.name} does not branch", ins.line)
        self._check_operand_count(op, len(operands), ins.line)
        return Encoded(op, operands, store, branch, text, line=ins.line)

    def _check_operand_count(self, op: Op, n: int, line: int) -> None:
        limits = {"2OP": (1, 4) if op.name == "je" else (2, 2), "1OP": (1, 1), "0OP": (0, 0),
                  "VAR": (0, 8 if op.name in DOUBLE_TYPE_BYTE else 4), "EXT": (0, 4)}
        lo, hi = limits[op.kind]
        if not lo <= n <= hi:
            raise self.error(f"{op.name} takes {lo}..{hi} operands, got {n}", line)

    def relax(self, encoded: list, routine: RoutineDef) -> dict[str, int]:
        """Grow branches from 1 to 2 bytes until all offsets fit (§4.7.2).
        Returns label -> offset from the routine's first instruction."""
        while True:
            labels, offset = {}, 0
            for item in encoded:
                if isinstance(item, Label):
                    labels[item.name] = offset
                else:
                    item.offset = offset
                    offset += item.size()
            changed = False
            for item in encoded:
                if isinstance(item, Label) or item.branch is None or item.long_branch:
                    continue
                target = item.branch[1]
                if target in ("rtrue", "rfalse"):
                    continue
                if target not in labels:
                    raise self.error(f"unknown label '{target}' in {routine.name}", item.line)
                jump = labels[target] - (item.offset + item.size()) + 2
                if not 2 <= jump <= 63:          # short form holds 0..63; 0/1 mean return
                    item.long_branch = True
                    changed = True
            if not changed:
                for item in encoded:
                    if isinstance(item, Encoded) and item.op.name == "jump":
                        if item.operands[0][1][1] not in labels:
                            raise self.error(f"unknown label '{item.operands[0][1][1]}'",
                                             item.line)
                return labels

    # ======================================================= pass 3: layout
    def assemble(self, text: str) -> bytes:
        """The whole pipeline, in the order of the memory map (§1.1):
        collect -> encode routines -> lay out dynamic, static and high
        memory (sizes only) -> fill in every value -> header -> checksum."""
        self.collect(text)
        if self.main not in {r.name for r in self.routines}:
            raise self.error(f"no main routine '{self.main}' (use .main NAME)", 1)
        routines = [(r, *self.encode_routine(r)) for r in self.routines]
        self._prescan_data_tokens()
        story = bytearray(H.HEADER_SIZE)
        layout = Layout()
        self._layout_dynamic(story, layout)
        self._layout_static(story, layout)
        self._layout_high(story, layout, routines)
        linker.check_size(len(story), self.profile)   # before packing anything (§1.1.4)
        self.resolving = True                       # pass 4: every address is known
        self._fill_data(story, layout)
        self._fill_code(story, layout)
        linker.write_header(story, linker.HeaderFields(
            release=self.release, serial=self.serial, high_memory=layout.high_memory,
            initial_pc=layout.stub, dictionary=layout.static_memory,
            objects=layout.object_table, globals=layout.globals_table,
            static_memory=layout.static_memory, abbreviations=layout.abbreviations,
            flags2=H.F2_UNDO if self.want_undo else 0,
            routines_offset=self.routines_offset, strings_offset=self.strings_offset), self.profile)
        return linker.finalise(story, self.profile)

    def _layout_dynamic(self, story: bytearray, layout: "Layout") -> None:
        """Dynamic memory: abbreviations, object table, globals, arrays."""
        layout.abbreviations = len(story)
        story += bytes(2 * linker.ABBREVIATION_COUNT)
        empty_string = len(story)
        story += encode_string("")
        for i in range(linker.ABBREVIATION_COUNT):   # all point at "" (a WORD address)
            story[layout.abbreviations + 2 * i:layout.abbreviations + 2 * i + 2] = \
                (empty_string // 2).to_bytes(2, "big")
        story += bytes(len(story) % 2)
        layout.object_table = len(story)
        story += bytes(2 * 63 + 14 * len(self.objects))   # defaults + 14-byte entries
        for obj in self.objects:
            layout.prop_addresses.append(len(story))
            story += bytes(linker.property_table_size(obj))
        layout.globals_table = len(story)
        story += bytes(2 * linker.GLOBAL_COUNT)
        for name, (kind, tokens) in self.arrays.items():
            self.addresses["array:" + name] = len(story)
            story += bytes(len(tokens) * (2 if kind == "word" else 1))
        story += bytes(len(story) % 2)

    def _layout_static(self, story: bytearray, layout: "Layout") -> None:
        """Static memory: the dictionary (read-only for the game, §1.1.2)."""
        layout.static_memory = len(story)
        dict_bytes, self.dict_addresses = linker.build_dictionary(
            self.words, self.separators, layout.static_memory)
        story += dict_bytes

    def _layout_high(self, story: bytearray, layout: "Layout", routines) -> None:
        """High memory: start stub, routines, then strings - each aligned
        so it has a packed address (§1.2.3; 4 bytes in v5)."""
        boundary = self.profile.code_alignment
        story += bytes(align(len(story), boundary) - len(story))
        layout.high_memory = layout.stub = len(story)
        story += bytes(8)                      # call_vn main (4 bytes) + quit + padding
        self.routines_offset = self._start_area(story)
        for routine, encoded, labels in routines:
            story += bytes(align(len(story), boundary) - len(story))
            address = len(story)
            self.addresses["routine:" + routine.name] = address
            size = 1 + sum(e.size() for e in encoded if isinstance(e, Encoded))
            layout.routine_places.append((address, routine, encoded, labels))
            story += bytes(size)
        self.strings_offset = self._start_area(story)
        for name, text in self.strings.items():  # interned while encoding: laid out last
            story += bytes(align(len(story), boundary) - len(story))
            self.addresses["string:" + name] = len(story)
            data = encode_string(text)
            layout.string_places.append((len(story), data))
            story += data

    def _start_area(self, story: bytearray) -> int:
        """Begin the routine or string area and return its offset (R_O or S_O).

        With packing offsets (v6/v7) the area starts on a multiple of 8, and
        the offset points ONE 8-byte step before it, so the first routine or
        string packs to P = 2, never to 0. Packed 0 is special: calling it
        does nothing and returns false (§6.4.3), and 0 in a property or
        table means "none". In the other versions the offset is 0."""
        if not self.profile.uses_packing_offsets:
            return 0
        story += bytes(align(len(story), self.profile.area_alignment) - len(story))
        return len(story) // 8 - 1

    def _fill_data(self, story: bytearray, layout: "Layout") -> None:
        """Pass 4a: objects, globals and arrays now that addresses exist."""
        for i, obj in enumerate(self.objects):
            table = linker.encode_property_table(obj, lambda t: self.value_of(t, obj.line))
            a = layout.prop_addresses[i]
            story[a:a + len(table)] = table
        self._emit_object_entries(story, layout.object_table, layout.prop_addresses)
        for number, init in self.globals.values():
            a = layout.globals_table + 2 * (number - 16)
            story[a:a + 2] = (self.value_of(init, 0) & 0xFFFF).to_bytes(2, "big")
        for name, (kind, tokens) in self.arrays.items():
            a = self.addresses["array:" + name]
            for token in tokens:
                v = self.value_of(token, 0)
                if kind == "word":
                    story[a:a + 2] = (v & 0xFFFF).to_bytes(2, "big")
                    a += 2
                else:
                    story[a] = v & 0xFF
                    a += 1

    def _fill_code(self, story: bytearray, layout: "Layout") -> None:
        """Pass 4b: the start stub, every routine body and every string."""
        main_packed = self.pack_routine(self.main)
        story[layout.stub:layout.stub + 5] = bytes(
            [0xF9, 0x3F, *main_packed.to_bytes(2, "big"), 0xBA])   # call_vn main; quit
        for address, routine, encoded, labels in layout.routine_places:
            story[address] = len(routine.locals)
            self._emit_routine(story, address + 1, encoded, labels)
        for address, data in layout.string_places:
            story[address:address + len(data)] = data

    def _prescan_data_tokens(self) -> None:
        """Strings and dictionary words used as DATA (property values, global
        initial values, array items) must exist before layout."""
        tokens = [init for _n, init in self.globals.values()]
        tokens += list(self.prop_defaults.values())
        for _kind, items in self.arrays.values():
            tokens += items
        for obj in self.objects:
            for _kind, items in obj.properties.values():
                tokens += items
        for token in tokens:
            if token.startswith('"'):
                self.intern_string(unquote(token))
            elif token.startswith("'") and unquote(token).lower() not in self.words:
                self.words.append(unquote(token).lower())

    def _emit_object_entries(self, story: bytearray, table: int, prop_addresses: list[int]) -> None:
        for number, token in self.prop_defaults.items():
            a = table + 2 * (number - 1)
            story[a:a + 2] = (self.value_of(token, 0) & 0xFFFF).to_bytes(2, "big")
        parent = {o.name: (self.value_of(o.parent, o.line) if o.parent != "0" else 0)
                  for o in self.objects}
        children: dict[int, list[int]] = {}
        for o in self.objects:
            children.setdefault(parent[o.name], []).append(self.object_numbers[o.name])
        for o in self.objects:
            n = self.object_numbers[o.name]
            siblings = children[parent[o.name]]
            index = siblings.index(n)
            sibling = siblings[index + 1] if index + 1 < len(siblings) else 0
            child = children.get(n, [0])[0]
            entry = linker.encode_object_entry(o.attributes, parent[o.name], sibling, child,
                                               prop_addresses[n - 1])
            a = table + 2 * 63 + 14 * (n - 1)
            story[a:a + 14] = entry

    # ================================================= symbol resolution
    def value_of(self, token: str, line: int) -> int:
        kind, value = self.operand(token, None, line)
        if kind == OperandType.VARIABLE:
            raise self.error(f"'{token}' is a variable, not a value", line)
        return value() if callable(value) else value

    def resolve_symbol(self, token: str, line: int) -> int:
        if "routine:" + token in self.addresses:
            return self.pack_routine(token)                            # §1.2.3
        if "string:" + token in self.addresses:
            return self.pack_string(token)
        if "array:" + token in self.addresses:
            return self.addresses["array:" + token]
        raise self.error(f"unknown symbol '{token}'", line)

    def packed(self, string_name: str, line: int) -> int:
        return self.pack_string(string_name)

    def pack_routine(self, name: str) -> int:
        return self.profile.pack_routine(self.addresses["routine:" + name], self.routines_offset)

    def pack_string(self, name: str) -> int:
        return self.profile.pack_string(self.addresses["string:" + name], self.strings_offset)

    def dict_address(self, word: str, line: int) -> int:
        return self.dict_addresses[word]

    # ============================================================== emit
    def _emit_routine(self, story: bytearray, start: int, encoded: list, labels: dict) -> None:
        for item in encoded:
            if isinstance(item, Label):
                continue
            address = start + item.offset
            data = self._encode_bytes(item, start, labels)
            assert len(data) == item.size(), (item.op.name, len(data), item.size())
            story[address:address + len(data)] = data

    def _encode_bytes(self, e: Encoded, start: int, labels: dict) -> bytes:
        values = []
        for t, v in e.operands:
            if isinstance(v, tuple) and v[0] == "jump":
                # §15 jump: target = address after instruction + offset - 2
                offset = labels[v[1]] - (e.offset + e.size()) + 2
                values.append((t, offset & 0xFFFF))
            else:
                values.append((t, v() if callable(v) else v))
        out = bytearray()
        form = e.form()
        n = e.op.number
        if form == "long":
            out.append(n | (0x40 if values[0][0] == OperandType.VARIABLE else 0)
                       | (0x20 if values[1][0] == OperandType.VARIABLE else 0))
        elif form == "short":
            t = values[0][0] if values else OperandType.OMITTED
            out.append(0x80 | (int(t) << 4) | n)
        elif form == "extended":
            out += bytes([0xBE, n])
        else:
            out.append((0xE0 if e.op.kind == "VAR" else 0xC0) | n)
        if form in ("variable", "extended"):
            types = [int(t) for t, _ in values]
            nbytes = 2 if e.op.name in DOUBLE_TYPE_BYTE else 1
            types += [3] * (4 * nbytes - len(types))
            for b in range(nbytes):
                chunk = types[4 * b:4 * b + 4]
                out.append((chunk[0] << 6) | (chunk[1] << 4) | (chunk[2] << 2) | chunk[3])
        for t, v in values:
            out += (v & 0xFFFF).to_bytes(2, "big") if t == OperandType.LARGE else bytes([v & 0xFF])
        if e.store is not None:
            out.append(e.store)
        if e.branch is not None:
            on_true, target = e.branch
            if target in ("rtrue", "rfalse"):
                offset = 1 if target == "rtrue" else 0
            else:
                offset = labels[target] - (e.offset + e.size()) + 2
            flag = 0x80 if on_true else 0
            if e.long_branch:
                offset &= 0x3FFF
                out += bytes([flag | (offset >> 8), offset & 0xFF])
            else:
                out.append(flag | 0x40 | offset)
        if e.text:
            out += e.text
        return bytes(out)


def assemble(text: str, source: str = "<zas>", version: int = DEFAULT_VERSION) -> bytes:
    return Assembler(source, version).assemble(text)
