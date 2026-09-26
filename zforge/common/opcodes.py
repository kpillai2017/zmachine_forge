"""§14 The complete table of version-5 opcodes - the SINGLE source of truth
shared by the decoder, the disassembler and the assembler.

GENERATED once from spec/opcodes.json (built by zbuilder from the spec's
§14 HTML tables) and then committed as plain, readable Python.
tests/test_opcodes.py checks it still matches spec/opcodes.json.

    kind   : "2OP" | "1OP" | "0OP" | "VAR" | "EXT"  (operand count, §4.3)
    number : opcode number within its kind (the "Hex" column)
    store  : instruction is followed by a store-variable byte (§4.6)
    branch : instruction is followed by branch data (§4.7)
    text   : instruction is followed by an inline z-string (§4.8)
"""
from __future__ import annotations

from dataclasses import dataclass

SPEC_FINGERPRINT = "c04c6f2ef72b3644"


@dataclass(frozen=True)
class Op:
    kind: str
    number: int
    name: str
    store: bool = False
    branch: bool = False
    text: bool = False

    @property
    def label(self) -> str:
        return f"{self.kind}:{self.number}"


OPCODES: list[Op] = [
    Op('2OP',  1, 'je', store=False, branch=True, text=False),  # je a b ?(label)
    Op('2OP',  2, 'jl', store=False, branch=True, text=False),  # jl a b ?(label)
    Op('2OP',  3, 'jg', store=False, branch=True, text=False),  # jg a b ?(label)
    Op('2OP',  4, 'dec_chk', store=False, branch=True, text=False),  # dec_chk (variable) value ?(label)
    Op('2OP',  5, 'inc_chk', store=False, branch=True, text=False),  # inc_chk (variable) value ?(label)
    Op('2OP',  6, 'jin', store=False, branch=True, text=False),  # jin obj1 obj2 ?(label)
    Op('2OP',  7, 'test', store=False, branch=True, text=False),  # test bitmap flags ?(label)
    Op('2OP',  8, 'or', store=True, branch=False, text=False),  # or a b -> (result)
    Op('2OP',  9, 'and', store=True, branch=False, text=False),  # and a b -> (result)
    Op('2OP', 10, 'test_attr', store=False, branch=True, text=False),  # test_attr object attribute ?(label)
    Op('2OP', 11, 'set_attr', store=False, branch=False, text=False),  # set_attr object attribute
    Op('2OP', 12, 'clear_attr', store=False, branch=False, text=False),  # clear_attr object attribute
    Op('2OP', 13, 'store', store=False, branch=False, text=False),  # store (variable) value
    Op('2OP', 14, 'insert_obj', store=False, branch=False, text=False),  # insert_obj object destination
    Op('2OP', 15, 'loadw', store=True, branch=False, text=False),  # loadw array word-index -> (result)
    Op('2OP', 16, 'loadb', store=True, branch=False, text=False),  # loadb array byte-index -> (result)
    Op('2OP', 17, 'get_prop', store=True, branch=False, text=False),  # get_prop object property -> (result)
    Op('2OP', 18, 'get_prop_addr', store=True, branch=False, text=False),  # get_prop_addr object property -> (result)
    Op('2OP', 19, 'get_next_prop', store=True, branch=False, text=False),  # get_next_prop object property -> (result)
    Op('2OP', 20, 'add', store=True, branch=False, text=False),  # add a b -> (result)
    Op('2OP', 21, 'sub', store=True, branch=False, text=False),  # sub a b -> (result)
    Op('2OP', 22, 'mul', store=True, branch=False, text=False),  # mul a b -> (result)
    Op('2OP', 23, 'div', store=True, branch=False, text=False),  # div a b -> (result)
    Op('2OP', 24, 'mod', store=True, branch=False, text=False),  # mod a b -> (result)
    Op('2OP', 25, 'call_2s', store=True, branch=False, text=False),  # call_2s routine arg1 -> (result)
    Op('2OP', 26, 'call_2n', store=False, branch=False, text=False),  # call_2n routine arg1
    Op('2OP', 27, 'set_colour', store=False, branch=False, text=False),  # set_colour foreground background
    Op('2OP', 28, 'throw', store=False, branch=False, text=False),  # throw value stack-frame
    Op('1OP',  0, 'jz', store=False, branch=True, text=False),  # jz a ?(label)
    Op('1OP',  1, 'get_sibling', store=True, branch=True, text=False),  # get_sibling object -> (result) ?(label)
    Op('1OP',  2, 'get_child', store=True, branch=True, text=False),  # get_child object -> (result) ?(label)
    Op('1OP',  3, 'get_parent', store=True, branch=False, text=False),  # get_parent object -> (result)
    Op('1OP',  4, 'get_prop_len', store=True, branch=False, text=False),  # get_prop_len property-address -> (result)
    Op('1OP',  5, 'inc', store=False, branch=False, text=False),  # inc (variable)
    Op('1OP',  6, 'dec', store=False, branch=False, text=False),  # dec (variable)
    Op('1OP',  7, 'print_addr', store=False, branch=False, text=False),  # print_addr byte-address-of-string
    Op('1OP',  8, 'call_1s', store=True, branch=False, text=False),  # call_1s routine -> (result)
    Op('1OP',  9, 'remove_obj', store=False, branch=False, text=False),  # remove_obj object
    Op('1OP', 10, 'print_obj', store=False, branch=False, text=False),  # print_obj object
    Op('1OP', 11, 'ret', store=False, branch=False, text=False),  # ret value
    Op('1OP', 12, 'jump', store=False, branch=False, text=False),  # jump ?(label)
    Op('1OP', 13, 'print_paddr', store=False, branch=False, text=False),  # print_paddr packed-address-of-string
    Op('1OP', 14, 'load', store=True, branch=False, text=False),  # load (variable) -> (result)
    Op('1OP', 15, 'call_1n', store=False, branch=False, text=False),  # call_1n routine
    Op('0OP',  0, 'rtrue', store=False, branch=False, text=False),  # rtrue
    Op('0OP',  1, 'rfalse', store=False, branch=False, text=False),  # rfalse
    Op('0OP',  2, 'print', store=False, branch=False, text=True),  # print (literal-string)
    Op('0OP',  3, 'print_ret', store=False, branch=False, text=True),  # print_ret (literal-string)
    Op('0OP',  4, 'nop', store=False, branch=False, text=False),  # nop
    Op('0OP',  7, 'restart', store=False, branch=False, text=False),  # restart
    Op('0OP',  8, 'ret_popped', store=False, branch=False, text=False),  # ret_popped
    Op('0OP',  9, 'catch', store=True, branch=False, text=False),  # catch -> (result)
    Op('0OP', 10, 'quit', store=False, branch=False, text=False),  # quit
    Op('0OP', 11, 'new_line', store=False, branch=False, text=False),  # new_line
    Op('0OP', 13, 'verify', store=False, branch=True, text=False),  # verify ?(label)
    Op('0OP', 15, 'piracy', store=False, branch=True, text=False),  # piracy ?(label)
    Op('VAR',  0, 'call_vs', store=True, branch=False, text=False),  # call_vs routine ...0 to 3 args... -> (result)
    Op('VAR',  1, 'storew', store=False, branch=False, text=False),  # storew array word-index value
    Op('VAR',  2, 'storeb', store=False, branch=False, text=False),  # storeb array byte-index value
    Op('VAR',  3, 'put_prop', store=False, branch=False, text=False),  # put_prop object property value
    Op('VAR',  4, 'aread', store=True, branch=False, text=False),  # aread text parse time routine -> (result)
    Op('VAR',  5, 'print_char', store=False, branch=False, text=False),  # print_char output-character-code
    Op('VAR',  6, 'print_num', store=False, branch=False, text=False),  # print_num value
    Op('VAR',  7, 'random', store=True, branch=False, text=False),  # random range -> (result)
    Op('VAR',  8, 'push', store=False, branch=False, text=False),  # push value
    Op('VAR',  9, 'pull', store=False, branch=False, text=False),  # pull (variable)
    Op('VAR', 10, 'split_window', store=False, branch=False, text=False),  # split_window lines
    Op('VAR', 11, 'set_window', store=False, branch=False, text=False),  # set_window window
    Op('VAR', 12, 'call_vs2', store=True, branch=False, text=False),  # call_vs2 routine ...0 to 7 args... -> (result)
    Op('VAR', 13, 'erase_window', store=False, branch=False, text=False),  # erase_window window
    Op('VAR', 14, 'erase_line', store=False, branch=False, text=False),  # erase_line value
    Op('VAR', 15, 'set_cursor', store=False, branch=False, text=False),  # set_cursor line column
    Op('VAR', 16, 'get_cursor', store=False, branch=False, text=False),  # get_cursor array
    Op('VAR', 17, 'set_text_style', store=False, branch=False, text=False),  # set_text_style style
    Op('VAR', 18, 'buffer_mode', store=False, branch=False, text=False),  # buffer_mode flag
    Op('VAR', 19, 'output_stream', store=False, branch=False, text=False),  # output_stream number table
    Op('VAR', 20, 'input_stream', store=False, branch=False, text=False),  # input_stream number
    Op('VAR', 21, 'sound_effect', store=False, branch=False, text=False),  # sound_effect number effect volume routine
    Op('VAR', 22, 'read_char', store=True, branch=False, text=False),  # read_char 1 time routine -> (result)
    Op('VAR', 23, 'scan_table', store=True, branch=True, text=False),  # scan_table x table len form -> (result)
    Op('VAR', 24, 'not', store=True, branch=False, text=False),  # not value -> (result)
    Op('VAR', 25, 'call_vn', store=False, branch=False, text=False),  # call_vn routine ...up to 3 args...
    Op('VAR', 26, 'call_vn2', store=False, branch=False, text=False),  # call_vn2 routine ...up to 7 args...
    Op('VAR', 27, 'tokenise', store=False, branch=False, text=False),  # tokenise text parse dictionary flag
    Op('VAR', 28, 'encode_text', store=False, branch=False, text=False),  # encode_text zscii-text length from coded-text
    Op('VAR', 29, 'copy_table', store=False, branch=False, text=False),  # copy_table first second size
    Op('VAR', 30, 'print_table', store=False, branch=False, text=False),  # print_table zscii-text width height skip
    Op('VAR', 31, 'check_arg_count', store=False, branch=True, text=False),  # check_arg_count argument-number
    Op('EXT',  0, 'save', store=True, branch=False, text=False),  # save table bytes name prompt -> (result)
    Op('EXT',  1, 'restore', store=True, branch=False, text=False),  # restore table bytes name prompt -> (result)
    Op('EXT',  2, 'log_shift', store=True, branch=False, text=False),  # log_shift number places -> (result)
    Op('EXT',  3, 'art_shift', store=True, branch=False, text=False),  # art_shift number places -> (result)
    Op('EXT',  4, 'set_font', store=True, branch=False, text=False),  # set_font font -> (result)
    Op('EXT',  9, 'save_undo', store=True, branch=False, text=False),  # save_undo -> (result)
    Op('EXT', 10, 'restore_undo', store=True, branch=False, text=False),  # restore_undo -> (result)
    Op('EXT', 11, 'print_unicode', store=False, branch=False, text=False),  # print_unicode char-number
    Op('EXT', 12, 'check_unicode', store=True, branch=False, text=False),  # check_unicode char-number -> (result)
    Op('EXT', 13, 'set_true_colour', store=False, branch=False, text=False),  # set_true_colour foreground background
]

# Lookups used by the decoder (by kind+number) and assembler (by name).
BY_KIND_NUMBER: dict[tuple[str, int], Op] = {(op.kind, op.number): op for op in OPCODES}
BY_NAME: dict[str, Op] = {op.name: op for op in OPCODES}

# call_vs2 and call_vn2 take up to 8 operands: they have TWO operand-type bytes (§4.4.3.1)
DOUBLE_TYPE_BYTE = {"call_vs2", "call_vn2"}
