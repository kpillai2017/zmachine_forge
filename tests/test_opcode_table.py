"""The hand-readable opcode table must agree with the spec's §14 table."""
import json

from tests.conftest import ROOT
from zforge.common.opcodes import BY_NAME, OPCODES
from zbuilder.tools.opcode_table import opcodes_for_version, parse_opcode_lines


def test_98_v5_opcodes_and_unique_names():
    assert len(OPCODES) == 98
    assert len(BY_NAME) == 98


def test_matches_extracted_spec_json():
    path = ROOT / "spec" / "opcodes.json"
    spec = {(o["kind"], o["number"]): o for o in json.loads(path.read_text())["opcodes"]}
    for op in OPCODES:
        s = spec[(op.kind, op.number)]
        assert (s["name"], s["store"], s["branch"]) == (op.name, op.store, op.branch), op


def test_extractor_rules_on_a_tiny_table():
    html = """<tr><td></td><td> * </td><td>0OP:181</td><td>5</td><td>1</td>
    <td>save ?(label)</td></tr>
    <tr><td></td><td></td><td></td><td></td><td>4</td><td>save -> (result)</td></tr>
    <tr><td></td><td></td><td></td><td></td><td>5</td><td>[illegal]</td></tr>
    <tr><td></td><td></td><td>1OP:140</td><td>C</td><td></td><td>jump ?(label)</td></tr>"""
    ops = {o.name: o for o in opcodes_for_version(parse_opcode_lines(html), 5)}
    assert "save" not in ops                 # illegal from v5 on
    assert ops["jump"].branch is False       # "?(label)" in jump's syntax is an OPERAND


def test_jump_is_not_a_branch_instruction():
    assert BY_NAME["jump"].branch is False
    assert BY_NAME["get_child"].store and BY_NAME["get_child"].branch
    assert BY_NAME["check_unicode"].store
