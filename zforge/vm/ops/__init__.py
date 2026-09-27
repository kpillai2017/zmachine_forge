"""§15 The opcode handlers, one module per family.

HANDLERS maps each opcode NAME (as in zforge.common.opcodes) to a plain
function handler(vm, *operand_values). It is written out explicitly - no
reflection - so you can read exactly which function runs for each opcode.
tests/test_opcodes.py checks every v5 opcode has a handler.

When the decoder (vm/decoder.py, §4) decodes an instruction, it extracts:
  - the opcode name (e.g. "add", "jz", "insert_obj")
  - the operand values (as unsigned 16-bit integers)
This module's handlers_for() returns the right table (HANDLERS or HANDLERS_V6
depending on the story version), and vm.machine looks up the opcode name and
calls the handler with the operand values. Each handler then interprets them
according to the Z-machine standard (many are signed, some are addresses, some
are indices into arrays or properties).
"""
from zforge.vm.ops import (arith, branch, calls, input, misc, objects, output, screen, tables,
                           v6, variables)

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

# §8.8: version 6 adds eighteen opcodes and changes the form of five it
# shares with version 5. Nothing is taken away, so this is the v5 table
# with those on top. tests/test_v6.py checks every v6 opcode has a handler.
HANDLERS_V6 = {
    **HANDLERS,
    # windows (§8.8.3)
    "get_wind_prop": v6.op_get_wind_prop, "put_wind_prop": v6.op_put_wind_prop,
    "window_style": v6.op_window_style, "window_size": v6.op_window_size,
    "move_window": v6.op_move_window, "scroll_window": v6.op_scroll_window,
    "set_margins": v6.op_set_margins, "mouse_window": v6.op_mouse_window,
    "read_mouse": v6.op_read_mouse, "make_menu": v6.op_make_menu,
    # pictures (§8.8.5) - none available, reported honestly
    "picture_data": v6.op_picture_data, "draw_picture": v6.op_draw_picture,
    "erase_picture": v6.op_erase_picture, "picture_table": v6.op_picture_table,
    # user stacks (§6.6)
    "push_stack": v6.op_push_stack, "pop_stack": v6.op_pop_stack,
    "pull": v6.op_pull_v6,
    # the rest
    "print_form": v6.op_print_form, "buffer_screen": v6.op_buffer_screen,
    # the same opcodes, with v6's extra operands (§15)
    "set_colour": v6.op_set_colour_v6, "set_cursor": v6.op_set_cursor_v6,
    "set_font": v6.op_set_font_v6, "sound_effect": v6.op_sound_effect_v6,
}


def handlers_for(version: int) -> dict:
    """The handler table a story of this version runs on (§14)."""
    from zforge.common.versions import profile_for
    return HANDLERS_V6 if profile_for(version).opcode_table == 6 else HANDLERS
