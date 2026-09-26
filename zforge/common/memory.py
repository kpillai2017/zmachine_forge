"""§1 The memory map.

A story file is loaded into one flat byte array:

    0x0000 .. static_start-1   DYNAMIC memory  (read/write; header lives at 0)
    static_start .. 0xFFFF     STATIC memory   (read-only)
    high_start .. end          HIGH memory     (routines and strings; may
                                                overlap static memory)

Words are big-endian (§1.1.1). Game code may only WRITE to dynamic memory
(§1.1.1.1); we enforce that. Reading beyond the file end is an error.
"""
from __future__ import annotations

from zforge.common.errors import ZMachineError


class Memory:
    def __init__(self, data: bytes | bytearray, static_start: int, high_start: int):
        self.data = bytearray(data)
        self.static_start = static_start
        self.high_start = high_start

    def __len__(self) -> int:
        return len(self.data)

    # -- reading -------------------------------------------------------
    def read_byte(self, address: int) -> int:
        if not 0 <= address < len(self.data):
            raise ZMachineError(f"read outside memory: 0x{address:x}")
        return self.data[address]

    def read_word(self, address: int) -> int:
        """Big-endian 16-bit word (§1.1.1)."""
        return (self.read_byte(address) << 8) | self.read_byte(address + 1)

    def read_bytes(self, address: int, length: int) -> bytes:
        if address < 0 or address + length > len(self.data):
            raise ZMachineError(f"read outside memory: 0x{address:x}+{length}")
        return bytes(self.data[address:address + length])

    # -- writing (dynamic memory only) --------------------------------------
    def write_byte(self, address: int, value: int) -> None:
        if not 0 <= address < self.static_start:
            raise ZMachineError(f"write outside dynamic memory: 0x{address:x}")
        self.data[address] = value & 0xFF

    def write_word(self, address: int, value: int) -> None:
        self.write_byte(address, (value >> 8) & 0xFF)
        self.write_byte(address + 1, value & 0xFF)

    def write_header_byte(self, address: int, value: int) -> None:
        """The INTERPRETER may set header fields the game can't (§11.1)."""
        self.data[address] = value & 0xFF

    def write_header_word(self, address: int, value: int) -> None:
        self.data[address] = (value >> 8) & 0xFF
        self.data[address + 1] = value & 0xFF
