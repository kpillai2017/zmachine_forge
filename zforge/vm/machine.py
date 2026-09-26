"""The ZMachine: loading a story, variables, calls, and the main loop.

Reading order for students:
  1. __init__ / _reset       - load the file, set interpreter header fields (§11)
  2. read_variable & friends - variable numbers 0 / 1-15 / 16-255 (§6.2)
  3. step                    - fetch, decode (§4), execute (§15 via ops/)
  4. call_routine / ret      - routine calls and returns (§5, §6.4)
  5. branch / store_result   - how instructions report results (§4.6, §4.7)
"""
from __future__ import annotations

import random
from collections import deque

from zforge.common import header as H
from zforge.common.errors import QuitGame, RestartGame, ZMachineError
from zforge.common.memory import Memory
from zforge.common.numbers import from_signed
from zforge.common.text import (Alphabets, UnicodeTable, decode_zchars, text_to_zscii,
                                unpack_zchars)
from zforge.vm.decoder import Instruction, OperandType, decode
from zforge.vm.frames import MAX_LOCALS, Frame
from zforge.vm.lexer import Dictionary
from zforge.vm.objects import ObjectTable
from zforge.vm.streams import OutputStreams

INTERPRETER_NUMBER = 6          # §11.1.3: "IBM PC" is a common neutral choice
INTERPRETER_VERSION = ord("Z")  # an ASCII letter in v4-5
STANDARD_REVISION = (1, 1)      # we aim at Standard 1.1


class ZMachine:
    def __init__(self, story: bytes, screen, seed: int | None = None,
                 transcript_path: str | None = None, trace_file=None, trace_depth: int = 20):
        self.story = bytes(story)                  # pristine copy (restart, verify, Quetzal)
        self.header = H.Header.parse(self.story)   # raises for non-v5 files
        self.screen = screen
        self.rng = random.Random(seed)
        self.trace_file = trace_file
        self.recent = deque(maxlen=trace_depth)    # last N instructions for error reports
        self.warnings: list[str] = []
        self.undo_states: list = []
        self.transcript_path = transcript_path
        self.steps = 0
        self._reset()

    # ------------------------------------------------------------------ setup
    def _reset(self, keep_flags2: int | None = None) -> None:
        h = self.header
        self.mem = Memory(self.story, h.static_memory, h.high_memory)
        self.objects = ObjectTable(self.mem, h.objects, warn=self.warn)
        self.alphabets = (Alphabets.from_table(self.mem.read_bytes(h.alphabet_table, 78))
                          if h.alphabet_table else Alphabets.default())
        self.unicode = self._load_unicode_table()
        self.dictionary = Dictionary.load(self.mem, h.dictionary)
        self.streams = OutputStreams(self.mem, self.screen, self.to_zscii, self.transcript_path)
        # v1-5: execution starts at a byte address with a dummy frame (§5.5)
        self.frames = [Frame(return_pc=0, locals=[], store_var=None, arg_count=0)]
        self.pc = h.initial_pc
        self.set_interpreter_header()
        if keep_flags2 is not None:     # §15 restart keeps transcript + fixed-pitch bits
            flags2 = self.mem.read_word(H.H_FLAGS2) & ~0b11
            self.mem.write_header_word(H.H_FLAGS2, flags2 | (keep_flags2 & 0b11))
        elif self.transcript_path:      # --transcript: record from the very start
            self.mem.write_header_word(H.H_FLAGS2, self.mem.read_word(H.H_FLAGS2) | H.F2_TRANSCRIPT)
        self.streams.set_transcript(bool(self.mem.read_word(H.H_FLAGS2) & H.F2_TRANSCRIPT))

    def _load_unicode_table(self) -> UnicodeTable:
        """§3.8.5.2: header extension word 3 may point at a custom table."""
        ext = self.header.extension_table
        if ext and self.mem.read_word(ext) >= H.HX_UNICODE_TABLE:
            table = self.mem.read_word(ext + 2 * H.HX_UNICODE_TABLE)
            if table:
                n = self.mem.read_byte(table)
                chars = "".join(chr(self.mem.read_word(table + 1 + 2 * i)) for i in range(n))
                return UnicodeTable(chars)
        return UnicodeTable()

    def set_interpreter_header(self) -> None:
        """§11: fields the interpreter must set after load/restore/restart."""
        m, s = self.mem, self.screen
        flags1 = H.F1_BOLD | H.F1_ITALIC | H.F1_FIXED
        if getattr(s, "supports_colour", False):
            flags1 |= H.F1_COLOURS
        m.write_header_byte(H.H_FLAGS1, flags1)          # no timed input, sound, pictures
        flags2 = m.read_word(H.H_FLAGS2)
        flags2 &= ~(H.F2_PICTURES | H.F2_MOUSE | H.F2_SOUND | H.F2_MENUS)   # can't provide
        m.write_header_word(H.H_FLAGS2, flags2)
        m.write_header_byte(H.H_INTERPRETER_NUMBER, INTERPRETER_NUMBER)
        m.write_header_byte(H.H_INTERPRETER_VERSION, INTERPRETER_VERSION)
        m.write_header_byte(H.H_SCREEN_HEIGHT_LINES, min(s.height, 255))
        m.write_header_byte(H.H_SCREEN_WIDTH_CHARS, min(s.width, 255))
        m.write_header_word(H.H_SCREEN_WIDTH_UNITS, s.width)     # 1 unit = 1 character
        m.write_header_word(H.H_SCREEN_HEIGHT_UNITS, s.height)
        m.write_header_byte(H.H_FONT_WIDTH_UNITS, 1)
        m.write_header_byte(H.H_FONT_HEIGHT_UNITS, 1)
        m.write_header_byte(H.H_DEFAULT_BACKGROUND, 2)          # black
        m.write_header_byte(H.H_DEFAULT_FOREGROUND, 9)          # white
        m.write_header_byte(H.H_STANDARD_REVISION, STANDARD_REVISION[0])
        m.write_header_byte(H.H_STANDARD_REVISION + 1, STANDARD_REVISION[1])

    def recent_trace(self) -> list[str]:
        """The last few instructions, for fatal-error reports (proforma §8b)."""
        return [format_trace(ins, depth) for ins, depth in self.recent]

    def warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)

    # -------------------------------------------------------------- variables
    @property
    def frame(self) -> Frame:
        return self.frames[-1]

    def _global_address(self, number: int) -> int:
        return self.header.globals + 2 * (number - 16)

    def read_variable(self, number: int) -> int:
        """§6.2: 0 = pop the stack, 1-15 = locals, 16-255 = globals."""
        if number == 0:
            return self.frame.pop()
        if number < 16:
            return self._local(number)
        return self.mem.read_word(self._global_address(number))

    def write_variable(self, number: int, value: int) -> None:
        """§6.2: writing variable 0 PUSHES onto the stack."""
        value = from_signed(value)
        if number == 0:
            self.frame.push(value)
        elif number < 16:
            self._check_local(number)
            self.frame.locals[number - 1] = value
        else:
            self.mem.write_word(self._global_address(number), value)

    def read_variable_in_place(self, number: int) -> int:
        """§6.3.4: INDIRECT variable references (inc, dec, load, store, pull,
        inc_chk, dec_chk) read the top of the stack without popping."""
        return self.frame.peek() if number == 0 else self.read_variable(number)

    def write_variable_in_place(self, number: int, value: int) -> None:
        """...and overwrite the top of the stack without pushing."""
        if number == 0:
            self.frame.poke(from_signed(value))
        else:
            self.write_variable(number, value)

    def _check_local(self, number: int) -> None:
        if number > len(self.frame.locals):
            raise ZMachineError(f"Local variable {number} does not exist in this routine",
                                self.current.address if self.current else None)

    def _local(self, number: int) -> int:
        self._check_local(number)
        return self.frame.locals[number - 1]

    # ------------------------------------------------------------- execution
    current: Instruction | None = None

    def skip_text(self, address: int) -> int:
        _zchars, end = unpack_zchars(self.mem.read_word, address)
        return end

    def operand_values(self, ins: Instruction) -> list[int]:
        """Evaluate operands in order (§4.2): variables are READ now,
        which pops the stack for variable 0."""
        return [self.read_variable(o.value) if o.type == OperandType.VARIABLE else o.value
                for o in ins.operands]

    def step(self) -> None:
        from zforge.vm.ops import HANDLERS           # the explicit opcode table
        ins = decode(self.mem.read_byte, self.pc, self.skip_text)
        self.current = ins
        self.pc = ins.next_address
        self.steps += 1
        self.recent.append((ins, len(self.frames) - 1))      # formatted only if needed
        if self.trace_file is not None:
            self.trace_file.write(format_trace(ins, len(self.frames) - 1) + "\n")
        handler = HANDLERS.get(ins.op.name)
        if handler is None:
            if ins.op.name.startswith("ext_unknown"):
                self.warn(f"ignored unknown extended opcode {ins.op.label} (§14.2.1)")
                return
            raise ZMachineError(f"No handler for {ins.op.name} ({ins.op.label})", ins.address)
        try:
            handler(self, *self.operand_values(ins))
        except TypeError as exc:           # wrong operand count for this opcode
            raise ZMachineError(f"Bad operands for {ins.op.name}: {exc}", ins.address) from None

    def run(self, max_steps: int | None = None) -> str:
        """Run until @quit / end of input / step cap. Returns the exit reason."""
        while True:
            try:
                while max_steps is None or self.steps < max_steps:
                    self.step()
                return "step limit reached"
            except QuitGame as q:
                self.screen.flush()
                self.streams.close()
                return str(q) or "quit"
            except RestartGame:
                flags2 = self.mem.read_word(H.H_FLAGS2)
                self.screen.erase_window(-1)
                self._reset(keep_flags2=flags2)

    # ---------------------------------------------------- results & branches
    def store_result(self, value: int) -> None:
        """§4.6: write the result to the instruction's store variable."""
        if self.current.store is None:
            raise ZMachineError(f"{self.current.op.name} has no store byte")
        self.write_variable(self.current.store, value)

    def branch(self, condition: bool) -> None:
        """§4.7: jump if condition == on_true. Offsets 0/1 mean rfalse/rtrue."""
        b = self.current.branch
        if bool(condition) != b.on_true:
            return
        if b.offset == 0:
            self.ret(0)
        elif b.offset == 1:
            self.ret(1)
        else:
            self.pc = self.current.next_address + b.offset - 2

    # ------------------------------------------------------- calls & returns
    def unpack_routine(self, packed: int) -> int:
        return packed * H.PACKED_ADDRESS_FACTOR_V5          # §1.2.3

    def unpack_string(self, packed: int) -> int:
        return packed * H.PACKED_ADDRESS_FACTOR_V5

    def call_routine(self, packed: int, args: list[int], store_var: int | None) -> None:
        """§6.4: call the routine at packed address `packed`.

        Calling address 0 does nothing and returns false (§6.4.3).
        In v5 the routine header is a single byte, the number of locals;
        there are NO initial values - locals start at 0 (§5.2.1).
        """
        if packed == 0:
            if store_var is not None:
                self.write_variable(store_var, 0)
            return
        address = self.unpack_routine(packed)
        n_locals = self.mem.read_byte(address)
        if n_locals > MAX_LOCALS:
            raise ZMachineError(f"Routine at 0x{address:x} claims {n_locals} locals (max 15)",
                                self.current.address if self.current else None)
        locals_ = [0] * n_locals
        for i, value in enumerate(args[:n_locals]):   # extra arguments are discarded
            locals_[i] = value
        self.frames.append(Frame(return_pc=self.pc, locals=locals_, store_var=store_var,
                                 arg_count=len(args)))
        self.pc = address + 1

    def ret(self, value: int) -> None:
        """§6.4.4: return `value` to the caller and resume after the call."""
        if len(self.frames) == 1:
            raise ZMachineError("Return from the main routine (§6.4)", self.pc)
        frame = self.frames.pop()
        self.pc = frame.return_pc
        if frame.store_var is not None:
            self.write_variable(frame.store_var, value)

    # ----------------------------------------------------------------- text
    def decode_string(self, address: int, allow_abbreviations: bool = True) -> str:
        zchars, _end = unpack_zchars(self.mem.read_word, address)
        return decode_zchars(zchars, self.alphabets, self.unicode,
                             self._abbreviation if allow_abbreviations else None)

    def _abbreviation(self, index: int) -> str:
        """§3.3: entry `index` of the abbreviations table is a WORD address."""
        word_address = self.mem.read_word(self.header.abbreviations + 2 * index)
        return self.decode_string(2 * word_address, allow_abbreviations=False)

    def to_zscii(self, text: str) -> list[int]:
        return text_to_zscii(text, self.unicode)

    def output(self, text: str) -> None:
        self.streams.write(text, self.screen.window)


def format_trace(ins: Instruction, depth: int) -> str:
    """One readable line per instruction, e.g.
    'PC=0x004d5 depth=2  2OP:je  L01 #05 ?+0x000a(T)  [§15 je]'"""
    parts = []
    for o in ins.operands:
        if o.type == OperandType.VARIABLE:
            parts.append(variable_name(o.value))
        else:
            parts.append(f"#{o.value:02x}" if o.type == OperandType.SMALL else f"#{o.value:04x}")
    if ins.store is not None:
        parts.append("-> " + variable_name(ins.store))
    if ins.branch is not None:
        target = {0: "rfalse", 1: "rtrue"}.get(ins.branch.offset, f"0x{ins.branch_target():05x}")
        parts.append(f"?{'' if ins.branch.on_true else '~'}{target}")
    return (f"PC=0x{ins.address:05x} depth={depth}  {ins.op.label:<7} "
            f"{ins.op.name:<14} {' '.join(parts)}")


def variable_name(number: int) -> str:
    if number == 0:
        return "sp"
    if number < 16:
        return f"L{number - 1:02d}"
    return f"G{number - 16:02x}"
