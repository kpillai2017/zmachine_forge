"""§4 How instructions are encoded.

An instruction is laid out as:

    opcode (1 or 2 bytes) | operand types | operands | store | branch | text

Four FORMS (§4.3), chosen by the top bits of the first byte:

    0xBE              extended form: next byte is the EXT opcode number
    11xxxxxx          variable form: bit 5 = 0 -> 2OP, 1 -> VAR; number = bits 0-4
    10xxxxxx          short form: bits 4-5 = operand type (11 -> 0OP, else 1OP);
                      number = bits 0-3
    0xxxxxxx          long form: always 2OP; bit 6/5 = type of operand 1/2
                      (0 = small constant, 1 = variable); number = bits 0-4

Operand types (§4.2): 00 large constant (word), 01 small constant (byte),
10 variable (byte: variable number), 11 omitted.

The decoder is PURE: it never executes anything, so the disassembler uses
it too. Variable operands are returned as variable NUMBERS; the machine
reads their values when executing (§4.2.2).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from zforge.common.errors import ZMachineError
from zforge.common.opcodes import BY_KIND_NUMBER, DOUBLE_TYPE_BYTE, Op

OpcodeTable = dict[tuple[str, int], Op]

EXTENDED_PREFIX = 0xBE


class OperandType(IntEnum):
    LARGE = 0b00      # 2-byte constant
    SMALL = 0b01      # 1-byte constant
    VARIABLE = 0b10   # 1-byte variable number
    OMITTED = 0b11


@dataclass
class Operand:
    type: OperandType
    value: int        # the constant, or the variable number


@dataclass
class Branch:
    on_true: bool     # branch when the condition is true (bit 7, §4.7.1)
    offset: int       # 0 = rfalse, 1 = rtrue, else a signed jump offset (§4.7.2)


@dataclass
class Instruction:
    address: int
    op: Op
    form: str                       # "long" | "short" | "variable" | "extended"
    operands: list[Operand]
    store: int | None = None        # variable number to store the result in
    branch: Branch | None = None
    text_address: int | None = None  # start of an inline z-string (print/print_ret)
    next_address: int = 0           # address of the following instruction

    def branch_target(self) -> int | None:
        """§4.7.2: target = address after the branch data + offset - 2."""
        if self.branch is None or self.branch.offset in (0, 1):
            return None
        return self.next_address + self.branch.offset - 2


def _types_from_byte(byte: int) -> list[OperandType]:
    """A type byte holds four 2-bit types, first operand in the top bits.
    The first 'omitted' ends the list (§4.4.3)."""
    types = []
    for shift in (6, 4, 2, 0):
        t = OperandType((byte >> shift) & 0b11)
        if t == OperandType.OMITTED:
            break
        types.append(t)
    return types


def decode(read_byte, address: int, skip_text=None, table: OpcodeTable | None = None,
           version: int = 5) -> Instruction:
    """Decode the instruction at `address`, in the order of §4.1:

        opcode (1-2 bytes) | operand types | operands | store | branch | text

    read_byte(addr) -> int reads memory.  skip_text(addr) -> addr returns the
    address after a z-string (needed to find the end of print/print_ret).
    `table` is the opcode set of the story's version (opcodes.table_for);
    it defaults to version 5's.
    """
    table = table if table is not None else BY_KIND_NUMBER
    form, kind, number, types, pc = _decode_opcode(read_byte, address, table)
    op = table.get((kind, number))
    if op is None:
        if kind == "EXT" and number >= 29:
            # §14.2.1: unknown EXT opcodes from 29 up are ignored, not fatal
            op = Op("EXT", number, f"ext_unknown_{number}")
        else:
            raise ZMachineError(f"Illegal opcode {kind}:{number} for version {version} "
                                f"(byte 0x{read_byte(address):02x}) (§14)", address)
    operands, pc = _read_operands(read_byte, pc, types)
    ins = Instruction(address, op, form, operands)
    if op.store:                                       # §4.6
        ins.store = read_byte(pc)
        pc += 1
    if op.branch:                                      # §4.7
        ins.branch, pc = _read_branch(read_byte, pc)
    if op.text:                                        # §4.8
        ins.text_address = pc
        pc = skip_text(pc) if skip_text else pc
    ins.next_address = pc
    return ins


def _decode_opcode(read_byte, pc: int, table: OpcodeTable):
    """§4.3: the top two bits of the first byte choose the FORM, which says
    where the opcode number and the operand types are."""
    first = read_byte(pc)
    pc += 1
    if first == EXTENDED_PREFIX:                        # §4.3.4
        number = read_byte(pc)
        types = _types_from_byte(read_byte(pc + 1))
        return "extended", "EXT", number, types, pc + 2
    if first >> 6 == 0b11:                             # §4.3.3 variable form
        kind = "VAR" if first & 0x20 else "2OP"
        number = first & 0x1F
        types = _types_from_byte(read_byte(pc))
        pc += 1
        op = table.get((kind, number))
        if op is not None and op.name in DOUBLE_TYPE_BYTE:
            types += _types_from_byte(read_byte(pc))    # §4.4.3.1
            pc += 1
        return "variable", kind, number, types, pc
    if first >> 6 == 0b10:                             # §4.3.1 short form
        t = OperandType((first >> 4) & 0b11)
        if t == OperandType.OMITTED:
            return "short", "0OP", first & 0x0F, [], pc
        return "short", "1OP", first & 0x0F, [t], pc
    # §4.3.2 long form: always 2OP; bits 6 and 5 give the two operand types
    types = [OperandType.VARIABLE if first & 0x40 else OperandType.SMALL,
             OperandType.VARIABLE if first & 0x20 else OperandType.SMALL]
    return "long", "2OP", first & 0x1F, types, pc


def _read_operands(read_byte, pc: int, types: list[OperandType]):
    """§4.2: large constants are 2 bytes, small constants and variables 1."""
    operands = []
    for t in types:
        if t == OperandType.LARGE:
            value = (read_byte(pc) << 8) | read_byte(pc + 1)
            pc += 2
        else:
            value = read_byte(pc)
            pc += 1
        operands.append(Operand(t, value))
    return operands, pc


def _read_branch(read_byte, pc: int):
    """§4.7: bit 7 = branch on true; bit 6 set = one byte, offset 0..63;
    else a 14-bit SIGNED offset spread over two bytes."""
    b = read_byte(pc)
    pc += 1
    on_true = bool(b & 0x80)
    if b & 0x40:
        offset = b & 0x3F
    else:
        offset = ((b & 0x3F) << 8) | read_byte(pc)
        pc += 1
        if offset & 0x2000:
            offset -= 0x4000
    return Branch(on_true, offset), pc
