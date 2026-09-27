"""§15 text output opcodes. All text goes through vm.output(), which routes
it to the output streams (§7)."""
from __future__ import annotations

from zforge.common.numbers import to_signed


def op_print(vm):
    """§15 print (0OP:178): print the z-string that follows the opcode."""
    vm.output(vm.decode_string(vm.current.text_address))


def op_print_ret(vm):
    """§15 print_ret (0OP:179): print inline string, new line, return true."""
    vm.output(vm.decode_string(vm.current.text_address) + "\n")
    vm.ret(1)


def op_new_line(vm):
    """§15 new_line (0OP:187)."""
    vm.output("\n")


def op_print_char(vm, zscii):
    """§15 print_char (VAR:229): print one ZSCII character."""
    vm.output(vm.unicode.zscii_to_str(zscii))


def op_print_num(vm, value):
    """§15 print_num (VAR:230): print a SIGNED number."""
    vm.output(str(to_signed(value)))


def op_print_addr(vm, address):
    """§15 print_addr (1OP:135): print the z-string at a BYTE address."""
    vm.output(vm.decode_string(address))


def op_print_paddr(vm, packed):
    """§15 print_paddr (1OP:141): print the z-string at a PACKED address."""
    vm.output(vm.decode_string(vm.unpack_string(packed)))


def op_print_obj(vm, obj):
    """§15 print_obj (1OP:138): print an object's short name (§12.4.1)."""
    if obj == 0:
        vm.warn("print_obj called with object 0")
        return
    vm.output(vm.decode_string(vm.objects.short_name_address(obj)))


def op_print_table(vm, text, width, height=1, skip=0):
    """§15 print_table (VAR:254): print a width x height rectangle of ZSCII
    text; after each row, skip `skip` bytes. In the upper window each row
    starts under the previous one; in the lower window we print a newline."""
    line, column = vm.screen.get_cursor()
    address = text
    for row in range(height):
        if row > 0:
            if vm.screen.window == 1:
                vm.screen.set_cursor(line + row, column)
            else:
                vm.output("\n")
        chars = [vm.mem.read_byte(address + i) for i in range(width)]
        vm.output("".join(vm.unicode.zscii_to_str(c) for c in chars))
        address += width + skip


def op_print_unicode(vm, char_number):
    """§15 print_unicode (EXT:11): print a Unicode character."""
    vm.output(chr(char_number) if char_number >= 32 else "?")


def op_check_unicode(vm, char_number):
    """§15 check_unicode (EXT:12): bit 0 = can print, bit 1 = can read.
    Control codes are never valid (§3.8.5.4.5)."""
    control = char_number < 32 or 127 <= char_number <= 159
    vm.store_result(0 if control else 0b11)


def op_output_stream(vm, number, table=0, width=0):
    """§15 output_stream (VAR:243): select (+n) or deselect (-n) a stream.
    Stream 3 needs a table address. Stream 2 also mirrors Flags 2 bit 0."""
    from zforge.common import header as H
    n = to_signed(number)
    # Stream 0 does nothing (no operation)
    if n == 0:
        return
    # Flush any buffered output before switching streams
    vm.screen.flush()
    # Select or deselect the stream
    vm.streams.select(n, table)
    # Stream 2 (transcript) also sets/clears Flags 2 bit 0 in the header
    if abs(n) == 2:
        flags2 = vm.mem.read_word(H.H_FLAGS2)
        flags2 = flags2 | H.F2_TRANSCRIPT if n > 0 else flags2 & ~H.F2_TRANSCRIPT
        vm.mem.write_header_word(H.H_FLAGS2, flags2)
