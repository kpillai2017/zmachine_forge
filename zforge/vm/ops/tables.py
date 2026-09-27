"""§15 memory/table opcodes: loadw loadb storew storeb copy_table scan_table.
Array addresses are computed as unsigned 16-bit sums (§15 loadw)."""
from __future__ import annotations

from zforge.common.numbers import to_signed


def op_loadw(vm, array, word_index):
    """§15 loadw (2OP:15): store the word at array + 2*word_index."""
    vm.store_result(vm.mem.read_word((array + 2 * word_index) & 0xFFFF))


def op_loadb(vm, array, byte_index):
    """§15 loadb (2OP:16): store the byte at array + byte_index."""
    vm.store_result(vm.mem.read_byte((array + byte_index) & 0xFFFF))


def op_storew(vm, array, word_index, value):
    """§15 storew (VAR:225)."""
    vm.mem.write_word((array + 2 * word_index) & 0xFFFF, value)


def op_storeb(vm, array, byte_index, value):
    """§15 storeb (VAR:226)."""
    vm.mem.write_byte((array + byte_index) & 0xFFFF, value)


def op_copy_table(vm, first, second, size):
    """§15 copy_table (VAR:253):
      second == 0      -> zero `size` bytes at first
      size > 0         -> copy so that overlapping regions are safe
      size < 0         -> copy |size| bytes FORWARDS even if that corrupts"""
    size = to_signed(size)
    # Zeroing: if destination is 0, fill the source range with zeros
    if second == 0:
        for i in range(abs(size)):
            vm.mem.write_byte(first + i, 0)
    # Safe copy: read all bytes first via a buffer, so overlaps do not corrupt
    elif size > 0:
        data = vm.mem.read_bytes(first, size)        # copy via a buffer: overlap-safe
        for i, b in enumerate(data):
            vm.mem.write_byte(second + i, b)
    # Unsafe forward copy: overwrites may corrupt source before it is read
    else:
        for i in range(-size):
            vm.mem.write_byte(second + i, vm.mem.read_byte(first + i))


def op_scan_table(vm, x, table, length, form=0x82):
    """§15 scan_table (VAR:247): search `length` fields for x. `form` bit 7 set
    = compare words, else bytes; bits 0-6 = field length. Store the address
    of the match (or 0) and branch if found."""
    # Extract the field size in bytes from bits 0-6
    field_length = form & 0x7F
    # Search each field: bit 7 of form determines word vs byte comparison
    for i in range(length):
        address = table + i * field_length
        value = vm.mem.read_word(address) if form & 0x80 else vm.mem.read_byte(address)
        # On match, store the address and branch
        if value == x:
            vm.store_result(address)
            vm.branch(True)
            return
    # No match: store 0 and do not branch
    vm.store_result(0)
    vm.branch(False)
