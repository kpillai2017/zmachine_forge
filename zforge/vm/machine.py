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
from zforge.common.opcodes import table_for
from zforge.vm.ops import handlers_for

INTERPRETER_NUMBER = 6          # §11.1.3: "IBM PC" is a common neutral choice
INTERPRETER_VERSION = ord("Z")  # an ASCII letter in v4-5
STANDARD_REVISION = (1, 1)      # we aim at Standard 1.1


class ZMachine:
    def __init__(self, story: bytes, screen, seed: int | None = None,
                 transcript_path: str | None = None, trace_file=None, trace_depth: int = 20):
        """Load a Z-machine story file and initialise the interpreter.

        Parse the header; set up memory, the object table, dictionary,
        and screens. The story file bytes are kept pristine for restart/verify.
        """
        self.story = bytes(story)                  # pristine copy (restart, verify, Quetzal)
        self.header = H.Header.parse(self.story)   # raises for unsupported versions
        self.opcode_table = table_for(self.header.version)   # §14, per version
        self.handlers = handlers_for(self.header.version)    # §15, per version
        self.mouse_window = 1                                # §15 mouse_window default
        self.screen = screen
        screen.on_resize = self.screen_resized       # the terminal may change size
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
        """Initialise or restart the machine: set up memory, objects, dictionary,
        streams, and the initial frame and PC."""
        h = self.header
        # Initialise memory from the story file, separating dynamic and static
        self.mem = Memory(self.story, h.static_memory, h.high_memory)
        self.objects = ObjectTable(self.mem, h.objects, warn=self.warn)
        self.alphabets = (Alphabets.from_table(self.mem.read_bytes(h.alphabet_table, 78))
                          if h.alphabet_table else Alphabets.default())
        self.unicode = self._load_unicode_table()
        self.dictionary = Dictionary.load(self.mem, h.dictionary)
        self.streams = OutputStreams(self.mem, self.screen, self.to_zscii, self.transcript_path)
        # §5.5: execution starts at a byte address, in a dummy frame with no
        # locals. §5.4: v6 instead CALLS the "main" routine whose packed
        # address is in $06 - so the dummy frame is the caller it never
        # returns to, and call_routine sets up main's locals.
        self.frames = [Frame(return_pc=0, locals=[], store_var=None, arg_count=0)]
        self.pc = h.initial_pc
        if h.profile.starts_with_main_routine:
            self.pc = 0                       # only a return would use it, and that is illegal
            self.call_routine(h.initial_pc, [], None)
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

    def write_screen_size(self) -> None:
        """§11 $20/$21 the screen in lines and characters, $22/$24 in units
        (one unit is one character here)."""
        m, s = self.mem, self.screen
        m.write_header_byte(H.H_SCREEN_HEIGHT_LINES, min(s.height, 255))
        m.write_header_byte(H.H_SCREEN_WIDTH_CHARS, min(s.width, 255))
        m.write_header_word(H.H_SCREEN_WIDTH_UNITS, s.width)
        m.write_header_word(H.H_SCREEN_HEIGHT_UNITS, s.height)

    def screen_resized(self, width: int, height: int) -> None:
        """The terminal changed size: tell the game (§11 header), and on v6
        ask it to redraw (§11 remarks: "may be set by modern interpreters
        after, for example, resizing the 'screen'")."""
        self.write_screen_size()
        if self.header.profile.redraw_request_bit:
            self.mem.write_header_word(H.H_FLAGS2, self.mem.read_word(H.H_FLAGS2) | H.F2_REDRAW)

    def set_interpreter_header(self) -> None:
        """§11: fields the interpreter must set after load/restore/restart."""
        m, s = self.mem, self.screen
        # Advertise capabilities: we support bold, italic, fixed-pitch, and optionally colour
        flags1 = H.F1_BOLD | H.F1_ITALIC | H.F1_FIXED
        if getattr(s, "supports_colour", False):
            flags1 |= H.F1_COLOURS
        m.write_header_byte(H.H_FLAGS1, flags1)          # no timed input, sound, pictures
        # Clear flags the interpreter cannot support
        flags2 = m.read_word(H.H_FLAGS2)
        flags2 &= ~(H.F2_PICTURES | H.F2_MOUSE | H.F2_SOUND | H.F2_MENUS)   # can't provide
        m.write_header_word(H.H_FLAGS2, flags2)
        # Identify this interpreter
        m.write_header_byte(H.H_INTERPRETER_NUMBER, INTERPRETER_NUMBER)
        m.write_header_byte(H.H_INTERPRETER_VERSION, INTERPRETER_VERSION)
        self.write_screen_size()
        # §11.1: one unit IS one character here, so the font is 1x1. Version 6
        # swaps these two bytes, which is why the header knows where they go.
        width_byte, height_byte = self.header.font_size_bytes()
        m.write_header_byte(width_byte, 1)
        m.write_header_byte(height_byte, 1)
        m.write_header_byte(H.H_DEFAULT_BACKGROUND, 2)          # black
        m.write_header_byte(H.H_DEFAULT_FOREGROUND, 9)          # white
        m.write_header_byte(H.H_STANDARD_REVISION, STANDARD_REVISION[0])
        m.write_header_byte(H.H_STANDARD_REVISION + 1, STANDARD_REVISION[1])

    def recent_trace(self) -> list[str]:
        """The last few instructions, for fatal-error reports (proforma §8b)."""
        return [format_trace(ins, depth) for ins, depth in self.recent]

    def warn(self, message: str) -> None:
        """Record a warning, without duplication."""
        if message not in self.warnings:
            self.warnings.append(message)

    # -------------------------------------------------------------- variables
    @property
    def frame(self) -> Frame:
        """Return the current call frame (the innermost routine)."""
        return self.frames[-1]

    def _global_address(self, number: int) -> int:
        """Compute the memory address of a global variable (16-255)."""
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
        """Verify that local variable number exists in this routine."""
        if number > len(self.frame.locals):
            raise ZMachineError(f"Local variable {number} does not exist in this routine",
                                self.current.address if self.current else None)

    def _local(self, number: int) -> int:
        """Retrieve the value of local variable number (1-15), with bounds checking."""
        self._check_local(number)
        return self.frame.locals[number - 1]

    # ------------------------------------------------------------- execution
    current: Instruction | None = None

    def skip_text(self, address: int) -> int:
        """Skip over a z-string at address; return the address after it."""
        _zchars, end = unpack_zchars(self.mem.read_word, address)
        return end

    def operand_values(self, ins: Instruction) -> list[int]:
        """Evaluate operands in order (§4.2): variables are READ now,
        which pops the stack for variable 0."""
        return [self.read_variable(o.value) if o.type == OperandType.VARIABLE else o.value
                for o in ins.operands]

    def step(self) -> None:
        """Fetch-decode-execute: one instruction cycle.

        §4: fetch and decode the instruction at pc (form, opcode, operands).
        §15: call the handler for this opcode with the operand values.
        The handler may call branch(), store_result(), call_routine(), ret().
        """
        handlers = self.handlers                    # the explicit opcode table
        # Fetch and decode the instruction at PC (§4)
        ins = decode(self.mem.read_byte, self.pc, self.skip_text, self.opcode_table,
                     self.header.version)
        self.current = ins
        # Move past this instruction for the next step
        self.pc = ins.next_address
        self.steps += 1
        self.recent.append((ins, len(self.frames) - 1))      # formatted only if needed
        if self.trace_file is not None:
            self.trace_file.write(format_trace(ins, len(self.frames) - 1) + "\n")
        # Execute the instruction by looking up its handler (§15)
        handler = handlers.get(ins.op.name)
        if handler is None:
            if ins.op.name.startswith("ext_unknown"):
                self.warn(f"ignored unknown extended opcode {ins.op.label} (§14.2.1)")
                return
            raise ZMachineError(f"No handler for {ins.op.name} ({ins.op.label})", ins.address)
        # Evaluate operands and call the handler
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
        # Offset 0 = rfalse, offset 1 = rtrue (§4.7.1)
        if b.offset == 0:
            self.ret(0)
        elif b.offset == 1:
            self.ret(1)
        else:
            # Jump to target = instruction end + offset - 2 (§4.7.2)
            self.pc = self.current.next_address + b.offset - 2

    # ------------------------------------------------------- calls & returns
    def unpack_routine(self, packed: int) -> int:
        """§1.2.3: packed routine address -> byte address (see VersionProfile)."""
        return self.header.profile.unpack_routine(packed, self.header.routines_offset)

    def unpack_string(self, packed: int) -> int:
        """§1.2.3: packed string address -> byte address (see VersionProfile)."""
        return self.header.profile.unpack_string(packed, self.header.strings_offset)

    def call_routine(self, packed: int, args: list[int], store_var: int | None) -> None:
        """§6.4: call the routine at packed address `packed`.

        Calling address 0 does nothing and returns false (§6.4.3).
        In v5 the routine header is a single byte, the number of locals;
        there are NO initial values - locals start at 0 (§5.2.1).
        """
        # Packed address 0 is a no-op that returns false
        if packed == 0:
            if store_var is not None:
                self.write_variable(store_var, 0)
            return
        # Unpack the routine address and read its local variable count (§5.2)
        address = self.unpack_routine(packed)
        n_locals = self.mem.read_byte(address)
        if n_locals > MAX_LOCALS:
            raise ZMachineError(f"Routine at 0x{address:x} claims {n_locals} locals (max 15)",
                                self.current.address if self.current else None)
        # Initialise locals to 0, and overwrite with supplied arguments
        locals_ = [0] * n_locals
        for i, value in enumerate(args[:n_locals]):   # extra arguments are discarded
            locals_[i] = value
        # Push a new frame with this routine's locals, and jump to its first instruction
        self.frames.append(Frame(return_pc=self.pc, locals=locals_, store_var=store_var,
                                 arg_count=len(args)))
        self.pc = address + 1

    def ret(self, value: int) -> None:
        """§6.4.4: return `value` to the caller and resume after the call."""
        if len(self.frames) == 1:
            raise ZMachineError("Return from the main routine (§6.4)", self.pc)
        # Pop the frame and restore PC to the call site
        frame = self.frames.pop()
        self.pc = frame.return_pc
        # Store the result if the call instruction asked for one
        if frame.store_var is not None:
            self.write_variable(frame.store_var, value)

    # ----------------------------------------------------------------- text
    def decode_string(self, address: int, allow_abbreviations: bool = True) -> str:
        """Decode a z-string (packed text) to Unicode, optionally expanding abbreviations."""
        zchars, _end = unpack_zchars(self.mem.read_word, address)
        return decode_zchars(zchars, self.alphabets, self.unicode,
                             self._abbreviation if allow_abbreviations else None)

    def _abbreviation(self, index: int) -> str:
        """§3.3: entry `index` of the abbreviations table is a WORD address."""
        word_address = self.mem.read_word(self.header.abbreviations + 2 * index)
        return self.decode_string(2 * word_address, allow_abbreviations=False)

    def to_zscii(self, text: str) -> list[int]:
        """Convert a Unicode string to ZSCII code points."""
        return text_to_zscii(text, self.unicode)

    def output(self, text: str) -> None:
        """Write text to the selected output stream(s) in the current window."""
        self.streams.write(text, self.screen.window)


def format_trace(ins: Instruction, depth: int) -> str:
    """One readable line per instruction, e.g.
    'PC=0x004d5 depth=2  2OP:je  L01 #05 ?+0x000a(T)  [§15 je]'"""
    parts = []
    # Format each operand: variable names as sp/L##/G##, constants as hex
    for o in ins.operands:
        if o.type == OperandType.VARIABLE:
            parts.append(variable_name(o.value))
        else:
            parts.append(f"#{o.value:02x}" if o.type == OperandType.SMALL else f"#{o.value:04x}")
    # Append the store target if any
    if ins.store is not None:
        parts.append("-> " + variable_name(ins.store))
    # Append the branch target if any
    if ins.branch is not None:
        target = {0: "rfalse", 1: "rtrue"}.get(ins.branch.offset, f"0x{ins.branch_target():05x}")
        parts.append(f"?{'' if ins.branch.on_true else '~'}{target}")
    return (f"PC=0x{ins.address:05x} depth={depth}  {ins.op.label:<7} "
            f"{ins.op.name:<14} {' '.join(parts)}")


def variable_name(number: int) -> str:
    """Convert a variable number to its readable name: sp, L##, or G##."""
    if number == 0:
        return "sp"
    if number < 16:
        return f"L{number - 1:02d}"
    return f"G{number - 16:02x}"
