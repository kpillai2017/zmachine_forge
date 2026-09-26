"""§15 The opcode handlers, one module per family.

HANDLERS maps each opcode NAME (as in zforge.common.opcodes) to a plain
function handler(vm, *operand_values). It is written out explicitly - no
reflection - so you can read exactly which function runs for each opcode.
tests/test_opcodes.py checks every v5 opcode has a handler.
"""
from zforge.vm.ops import (arith, branch, calls, input, misc, objects, output, screen, tables,
                           variables)

HANDLERS = {
    # arithmetic / bitwise
    "add": arith.op_add, "sub": arith.op_sub, "mul": arith.op_mul,
    "div": arith.op_div, "mod": arith.op_mod, "or": arith.op_or,
    "and": arith.op_and, "not": arith.op_not,
    "log_shift": arith.op_log_shift, "art_shift": arith.op_art_shift,
    # branches and jumps
    "je": branch.op_je, "jl": branch.op_jl, "jg": branch.op_jg, "jz": branch.op_jz,
    "test": branch.op_test, "jump": branch.op_jump,
    "check_arg_count": branch.op_check_arg_count, "piracy": branch.op_piracy,
    # variables and the stack
    "inc": variables.op_inc, "dec": variables.op_dec,
    "inc_chk": variables.op_inc_chk, "dec_chk": variables.op_dec_chk,
    "load": variables.op_load, "store": variables.op_store,
    "push": variables.op_push, "pull": variables.op_pull,
    # calls and returns
    "call_1s": calls.op_call_1s, "call_1n": calls.op_call_1n,
    "call_2s": calls.op_call_2s, "call_2n": calls.op_call_2n,
    "call_vs": calls.op_call_vs, "call_vn": calls.op_call_vn,
    "call_vs2": calls.op_call_vs2, "call_vn2": calls.op_call_vn2,
    "ret": calls.op_ret, "rtrue": calls.op_rtrue, "rfalse": calls.op_rfalse,
    "ret_popped": calls.op_ret_popped, "catch": calls.op_catch, "throw": calls.op_throw,
    # objects
    "jin": objects.op_jin, "test_attr": objects.op_test_attr,
    "set_attr": objects.op_set_attr, "clear_attr": objects.op_clear_attr,
    "insert_obj": objects.op_insert_obj, "remove_obj": objects.op_remove_obj,
    "get_parent": objects.op_get_parent, "get_child": objects.op_get_child,
    "get_sibling": objects.op_get_sibling, "get_prop": objects.op_get_prop,
    "get_prop_addr": objects.op_get_prop_addr, "get_next_prop": objects.op_get_next_prop,
    "get_prop_len": objects.op_get_prop_len, "put_prop": objects.op_put_prop,
    # tables / memory
    "loadw": tables.op_loadw, "loadb": tables.op_loadb,
    "storew": tables.op_storew, "storeb": tables.op_storeb,
    "copy_table": tables.op_copy_table, "scan_table": tables.op_scan_table,
    # text output
    "print": output.op_print, "print_ret": output.op_print_ret,
    "new_line": output.op_new_line, "print_char": output.op_print_char,
    "print_num": output.op_print_num, "print_addr": output.op_print_addr,
    "print_paddr": output.op_print_paddr, "print_obj": output.op_print_obj,
    "print_table": output.op_print_table, "print_unicode": output.op_print_unicode,
    "check_unicode": output.op_check_unicode, "output_stream": output.op_output_stream,
    # input
    "aread": input.op_aread, "read_char": input.op_read_char,
    "tokenise": input.op_tokenise, "encode_text": input.op_encode_text,
    "input_stream": input.op_input_stream,
    # screen
    "split_window": screen.op_split_window, "set_window": screen.op_set_window,
    "erase_window": screen.op_erase_window, "erase_line": screen.op_erase_line,
    "set_cursor": screen.op_set_cursor, "get_cursor": screen.op_get_cursor,
    "set_text_style": screen.op_set_text_style, "buffer_mode": screen.op_buffer_mode,
    "set_colour": screen.op_set_colour, "set_true_colour": screen.op_set_true_colour,
    "set_font": screen.op_set_font, "sound_effect": screen.op_sound_effect,
    # miscellaneous
    "nop": misc.op_nop, "quit": misc.op_quit, "restart": misc.op_restart,
    "verify": misc.op_verify, "random": misc.op_random,
    "save": misc.op_save, "restore": misc.op_restore,
    "save_undo": misc.op_save_undo, "restore_undo": misc.op_restore_undo,
}
