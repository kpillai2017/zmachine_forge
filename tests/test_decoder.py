"""§4: instruction forms, operand types, store and branch encoding."""
from zforge.vm.decoder import OperandType, decode


def dec(*bytes_):
    data = bytes(bytes_) + bytes(8)
    return decode(lambda a: data[a], 0)


def test_long_form_2op_with_store():
    ins = dec(0x34, 0x05, 0x10, 0x00)          # add #5 G00 -> sp  (2OP:20, bit 5 = variable)
    assert ins.op.name == "add" and ins.form == "long"
    assert [o.type for o in ins.operands] == [OperandType.SMALL, OperandType.VARIABLE]
    assert ins.store == 0 and ins.next_address == 4


def test_short_branch_on_false_and_long_negative_branch():
    ins = dec(0xA0, 0x01, 0x45)                # jz L00 ?~(+5)  one-byte offset
    assert ins.op.name == "jz" and not ins.branch.on_true and ins.branch.offset == 5
    ins = dec(0xA0, 0x01, 0xBF, 0xF0)          # 14-bit signed: 0x3FF0 -> -16
    assert ins.branch.on_true and ins.branch.offset == -16


def test_variable_form_2op_and_var_and_ext():
    ins = dec(0xC1, 0x55, 0x01, 0x02, 0x03, 0x04, 0x40)   # je with 4 small operands
    assert ins.op.name == "je" and len(ins.operands) == 4
    ins = dec(0xBE, 0x09, 0xFF, 0x00)                     # save_undo -> sp
    assert ins.op.name == "save_undo" and ins.store == 0 and ins.form == "extended"


def test_call_vs2_reads_two_type_bytes():
    # types 0x15 = large,small,small,small ; 0x5F = small,small,(omitted)
    ins = dec(0xEC, 0x15, 0x5F, 0x12, 0x34, 1, 2, 3, 4, 5, 0x00)
    assert ins.op.name == "call_vs2" and len(ins.operands) == 6
    assert ins.operands[0].value == 0x1234 and ins.store == 0 and ins.next_address == 11
