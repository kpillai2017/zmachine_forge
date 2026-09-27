"""The disassembler: story file -> readable listing.

It uses the SAME decoder as the interpreter (zforge.vm.decoder), so what
you see is exactly what the VM executes.

Finding code without symbols is the hard part. We start at the initial PC
and follow every `call_*` whose routine operand is a constant, plus every
branch/jump target, until no new code is found (a "recursive descent"
disassembler, like txd).
"""
from __future__ import annotations

from zforge.common.header import Header
from zforge.common.memory import Memory
from zforge.common.numbers import to_signed
from zforge.common.text import Alphabets, UnicodeTable, decode_zchars, unpack_zchars
from zforge.vm.decoder import OperandType, decode
from zforge.vm.machine import variable_name
from zforge.common.opcodes import table_for

ENDS_ROUTINE = {"rtrue", "rfalse", "ret", "ret_popped", "print_ret", "quit", "jump",
                "restart", "throw"}
INDIRECT_FIRST = {"inc", "dec", "inc_chk", "dec_chk", "load", "store", "pull"}
CALLS = {"call_1s", "call_1n", "call_2s", "call_2n", "call_vs", "call_vn",
         "call_vs2", "call_vn2"}


class Disassembler:
    """Disassemble a story file to readable Z-code instructions."""
    def __init__(self, story: bytes):
        self.header = Header.parse(story)
        self.profile = self.header.profile      # packed addresses (§1.2.3)
        self.opcodes = table_for(self.header.version)   # §14
        self.mem = Memory(story, self.header.static_memory, self.header.high_memory)
        self.alphabets = Alphabets.default()
        self.unicode = UnicodeTable()

    def text_at(self, address: int) -> tuple[str, int]:
        """Decode a packed string at this address; return the text and next address."""
        zchars, end = unpack_zchars(self.mem.read_word, address)
        return decode_zchars(zchars, self.alphabets, self.unicode, self._abbreviation), end

    def _abbreviation(self, index: int) -> str:
        word_address = self.mem.read_word(self.header.abbreviations + 2 * index)
        zchars, _ = unpack_zchars(self.mem.read_word, 2 * word_address)
        return decode_zchars(zchars, self.alphabets, self.unicode, None)

    def skip_text(self, address: int) -> int:
        """Return the address after a packed string at this address."""
        return self.text_at(address)[1]

    # ------------------------------------------------------------- routines
    def routine(self, address: int, has_header: bool = True) -> list[str]:
        """Disassemble one routine starting at `address` (its header byte)."""
        lines = []
        pc = address
        if has_header:
            n_locals = self.mem.read_byte(address)
            lines.append(f"{address:05x}: routine  locals={n_locals}")
            pc += 1
        furthest = pc
        while True:
            ins = decode(self.mem.read_byte, pc, self.skip_text, self.opcodes,
                         self.header.version)
            lines.append(self.format(ins))
            target = ins.branch_target()
            if ins.op.name == "jump":
                target = ins.next_address + to_signed(ins.operands[0].value) - 2
            if target is not None:
                furthest = max(furthest, target)
            pc = ins.next_address
            if ins.op.name in ENDS_ROUTINE and pc > furthest:
                return lines

    def format(self, ins) -> str:
        """Format one instruction as a readable line."""
        raw = self.mem.read_bytes(ins.address, min(ins.next_address - ins.address, 8)).hex(" ")
        parts = []
        for i, o in enumerate(ins.operands):
            if o.type == OperandType.VARIABLE:
                parts.append(variable_name(o.value))
            elif ins.op.name == "jump":
                parts.append(f"0x{ins.next_address + to_signed(o.value) - 2:05x}")
            elif i == 0 and ins.op.name in INDIRECT_FIRST:
                parts.append(variable_name(o.value))     # a variable NUMBER (§6.3.4)
            elif i == 0 and ins.op.name in CALLS:
                address = self.profile.unpack_routine(o.value, self.header.routines_offset)
                parts.append(f"routine@0x{address:05x}")
            else:
                parts.append(str(o.value))
        if ins.store is not None:
            parts.append("-> " + variable_name(ins.store))
        if ins.branch is not None:
            t = {0: "rfalse", 1: "rtrue"}.get(ins.branch.offset)
            t = t or f"0x{ins.branch_target():05x}"
            parts.append(("?" if ins.branch.on_true else "?~") + t)
        if ins.text_address is not None:
            parts.append(repr(self.text_at(ins.text_address)[0]))
        return f"{ins.address:05x}: {raw:<24} {ins.op.name:<14} {' '.join(parts)}"

    def all_code(self) -> list[str]:
        """Recursive descent from the initial PC through constant calls."""
        seen: set[int] = set()
        pending = [(self.header.initial_pc, False)]
        out: list[str] = []
        while pending:
            address, has_header = pending.pop(0)
            if address in seen or not 0 < address < len(self.mem):
                continue
            seen.add(address)
            try:
                lines = self.routine(address, has_header)
            except Exception as exc:              # data mistaken for code
                out.append(f"{address:05x}: <cannot decode: {exc}>")
                continue
            out += lines + [""]
            # Queue any constant call targets found in this routine.
            for line in lines:
                if "routine@0x" in line:
                    target = int(line.split("routine@0x")[1].split()[0], 16)
                    if target and target not in seen:
                        pending.append((target, True))
        return out


def disassemble(story: bytes, routine: int | None = None) -> str:
    """Disassemble a story file to a readable string. If routine is given,
    disassemble that routine only; otherwise disassemble all reachable code."""
    d = Disassembler(story)
    lines = d.routine(routine) if routine is not None else d.all_code()
    return "\n".join(lines)
