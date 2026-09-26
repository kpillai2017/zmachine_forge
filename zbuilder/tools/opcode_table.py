"""Tool 3: extract_opcode_table - parse the §14 opcode tables into JSON.

How §14 is laid out (see "Reading the opcode tables"):
  * each <tr> has cells: St | Br | Opcode (TYPE:decimal) | Hex | V | name+syntax | link
  * "St"/"Br" contain '*' when the instruction stores a result / branches
  * V is the version the line's specification belongs to ("" = all
    versions; "5/3" = belongs to v5, first seen in v3). An opcode whose
    meaning changes has several lines; continuation lines leave the Opcode
    cell empty. "[illegal]" marks a version where it becomes illegal again.

The extraction is DETERMINISTIC (no LLM). An LLM may only review the diff.
"""
from __future__ import annotations

import html
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

KIND_BASE = {"2OP": 0, "1OP": 128, "0OP": 176, "VAR": 224, "EXT": 0}
# Opcodes that are followed by an inline z-encoded string (§4.8)
TEXT_OPCODES = {"print", "print_ret"}


@dataclass
class OpcodeLine:
    kind: str          # 2OP / 1OP / 0OP / VAR / EXT
    number: int        # opcode number within its kind (the Hex column)
    decimal: int       # the TYPE:Decimal value quoted in the table
    version: int       # first version this line's specification applies to
    name: str
    syntax: str
    store: bool
    branch: bool
    text: bool
    illegal: bool
    anchor: str        # link into §15, e.g. "sect15.html#je"


def _cell_text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", fragment)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def parse_opcode_lines(sect14_html: str) -> list[OpcodeLine]:
    # The "Inform assembly language" table at the end of §14 reuses the same
    # row layout; only the opcode tables BEFORE it are parsed.
    cut = re.search(r'<(?:a\s+name|h2\s+id)="inform"', sect14_html, flags=re.I)
    if cut:
        sect14_html = sect14_html[:cut.start()]
    lines: list[OpcodeLine] = []
    current: tuple[str, int, int] | None = None
    for row in re.findall(r"<tr>(.*?)</tr>", sect14_html, flags=re.S | re.I):
        raw_cells = re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.S | re.I)
        if len(raw_cells) < 6:
            continue
        cells = [_cell_text(c) for c in raw_cells]
        st, br, opcode, hexnum, ver, name_syntax = cells[:6]
        anchor_match = re.search(r'href="(sect15\.html#[^"]+)"', row)
        if ver == "V" or name_syntax.startswith("Inform name"):
            current = None               # a repeated column-header row
            continue
        m = re.fullmatch(r"(2OP|1OP|0OP|VAR|EXT):(\d+)", opcode)
        if m:
            current = (m.group(1), int(hexnum, 16), int(m.group(2)))
        elif opcode.startswith("---") or not name_syntax or name_syntax == "---":
            if opcode.startswith("---"):
                current = None          # an unused slot
            continue
        if current is None:
            continue
        kind, number, decimal = current
        version = int(ver.split("/")[0]) if ver and ver[0].isdigit() else 1
        illegal = "illegal" in name_syntax.lower()
        if name_syntax.lower().startswith("[first"):  # "[first byte of extended opcode]"
            continue
        name = name_syntax.split()[0] if not illegal else "[illegal]"
        lines.append(OpcodeLine(
            kind=kind, number=number, decimal=decimal, version=version,
            name=name, syntax=name_syntax, store=(st == "*" or "->" in name_syntax),
            # Br column only: "jump ?(label)" is NOT a branch - its label is an operand
            branch=(br == "*"),
            text=name in TEXT_OPCODES, illegal=illegal,
            anchor=anchor_match.group(1) if anchor_match else ""))
    return lines


def opcodes_for_version(lines: list[OpcodeLine], version: int) -> list[OpcodeLine]:
    """For each (kind, number) pick the LAST line whose version <= target.
    Drop it if that line is marked [illegal]."""
    chosen: dict[tuple[str, int], OpcodeLine] = {}
    for line in lines:
        if line.version <= version:
            chosen[(line.kind, line.number)] = line
    return [op for op in chosen.values() if not op.illegal]


# §1 (end of section): "Throughout the specification, Versions 7 and 8 are
# identical to Version 5 except as stated at 1.1.4 and 1.2.3" - i.e. only
# the size limit and packed addresses differ, NOT the opcode set. Reading
# §14's V column literally ("last line with V <= target") would wrongly give
# v7/v8 every v6-only opcode, so v7/v8 read the table AS version 5.
SUPPORTED_VERSIONS = (5, 6, 7, 8)
TABLE_VERSION = {5: 5, 6: 6, 7: 5, 8: 5}


def opcodes_for_zversion(lines: list[OpcodeLine], version: int) -> list[OpcodeLine]:
    """The opcode set of a story-file version, applying the §1 rule above."""
    ops = opcodes_for_version(lines, TABLE_VERSION[version])
    ops.sort(key=lambda o: (list(KIND_BASE).index(o.kind), o.number))
    return ops


def merge_versions(lines: list[OpcodeLine]) -> list[dict]:
    """One entry per distinct opcode SPECIFICATION, with the versions it is
    valid in. An opcode whose meaning changes (e.g. VAR:9 pull, which stores
    a result only in v6) appears twice, once per meaning."""
    merged: dict[tuple, dict] = {}
    for version in SUPPORTED_VERSIONS:
        for op in opcodes_for_zversion(lines, version):
            key = (op.kind, op.number, op.syntax)
            entry = merged.setdefault(key, {**asdict(op), "versions": []})
            entry["versions"].append(version)
    return sorted(merged.values(), key=lambda e: (list(KIND_BASE).index(e["kind"]),
                                                  e["number"], e["versions"]))


def build_opcode_json(sect14_path: Path, out_path: Path, version: int = 5,
                      fingerprint: str = "") -> dict:
    """Write spec/opcodes.json.

    "opcodes" is the v5 view exactly as zforge v1 used it (unchanged keys
    and order). "all_versions" adds every opcode of versions 5-8 with a
    `versions` list, and "counts" gives the size of each version's set.
    """
    lines = parse_opcode_lines(sect14_path.read_text(encoding="latin-1"))
    ops = opcodes_for_version(lines, version)
    ops.sort(key=lambda o: (list(KIND_BASE).index(o.kind), o.number))
    data = {
        "source": "Z-Machine Standard 1.1 §14",
        "version": version,
        "spec_fingerprint": fingerprint,
        "all_lines": len(lines),
        "count": len(ops),
        "opcodes": [asdict(o) for o in ops],
        "version_rule": "§1: versions 7 and 8 use the version-5 opcode set",
        "counts": {str(v): len(opcodes_for_zversion(lines, v)) for v in SUPPORTED_VERSIONS},
        "all_versions": merge_versions(lines),
    }
    out_path.write_text(json.dumps(data, indent=1))
    return data
