"""Tokenising and parsing .zas assembly text into records.

A .zas file is a list of lines. Each line is one of:

    ; comment
    .directive args...              (see DIRECTIVES below)
    label:                          (inside a routine)
    opcode operand... [-> store] [?[~]label]

Operands:
    42  -1  $2a  0x2a               numbers
    sp  L00..L14  G00..Gef          variables (stack, locals, globals)
    name                            a local/global/constant/object/routine/
                                    string/array symbol
    'word'                          a dictionary word (its address)
    "text"                          a string: inline for print/print_ret,
                                    otherwise a packed string address
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from zforge.common.errors import ZForgeError

DIRECTIVES = {
    ".release", ".serial", ".global", ".constant", ".array", ".buffer",
    ".object", ".prop", ".propb", ".propdefault", ".dict", ".separators",
    ".string", ".routine", ".end", ".main", ".undo",
}

TOKEN_RE = re.compile(r'''
      "(?:[^"\\]|\\.)*"       # "string" (\" and \\ escapes, ^ = newline)
    | '(?:[^'\\]|\\.)*'       # 'dictionary word'
    | ->                      # store arrow
    | \?~?[^\s]+              # branch target
    | [^\s]+                  # anything else
''', re.X)


class AsmError(ZForgeError):
    def __init__(self, message: str, line: int, source: str = "<zas>"):
        super().__init__(f"{source}:{line}: {message}")
        self.line = line


@dataclass
class Directive:
    name: str
    args: list[str]
    line: int


@dataclass
class AsmInstruction:
    opcode: str
    operands: list[str]
    store: str | None
    branch: str | None          # e.g. "?loop", "?~done", "?rtrue"
    line: int


@dataclass
class Label:
    name: str
    line: int


@dataclass
class Program:
    """Everything in a .zas file, in order."""
    items: list = field(default_factory=list)


def unquote(token: str) -> str:
    """'"Hello^world"' -> 'Hello\\nworld'. ^ is a newline, as in Inform/ZIL."""
    body = token[1:-1]
    out, i = [], 0
    while i < len(body):
        c = body[i]
        if c == "\\" and i + 1 < len(body):
            out.append(body[i + 1])
            i += 2
            continue
        out.append("\n" if c == "^" else c)
        i += 1
    return "".join(out)


def tokenize_line(text: str) -> list[str]:
    """Split a line into tokens, respecting strings, dictionary words and comments."""
    tokens, pos = [], 0
    while pos < len(text):
        if text[pos].isspace():
            pos += 1
            continue
        # Semicolon starts a comment; ignore to end of line.
        if text[pos] == ";":
            break                                # comment to end of line
        m = TOKEN_RE.match(text, pos)
        tokens.append(m.group(0))
        pos = m.end()
    return tokens


def parse(text: str, source: str = "<zas>") -> Program:
    """Parse .zas assembly text into a program: directives, labels and instructions."""
    program = Program()
    for number, raw in enumerate(text.splitlines(), start=1):
        tokens = tokenize_line(raw)
        if not tokens:
            continue
        # Classify the line: directive, label or instruction.
        head = tokens[0]
        if head.startswith("."):
            if head not in DIRECTIVES:
                raise AsmError(f"unknown directive {head}", number, source)
            program.items.append(Directive(head, tokens[1:], number))
        elif head.endswith(":") and len(tokens) == 1:
            program.items.append(Label(head[:-1], number))
        else:
            program.items.append(_parse_instruction(tokens, number, source))
    return program


def _parse_instruction(tokens: list[str], line: int, source: str) -> AsmInstruction:
    """Parse one instruction line into an AsmInstruction record."""
    opcode, rest = tokens[0], tokens[1:]
    store = branch = None
    operands: list[str] = []
    i = 0
    # Extract operands, store and branch from the token stream.
    while i < len(rest):
        t = rest[i]
        if t == "->":
            if i + 1 >= len(rest):
                raise AsmError("'->' needs a variable", line, source)
            store = rest[i + 1]
            i += 2
            continue
        # Branch target: ?label or ?~label.
        if t.startswith("?") and not t.startswith(('"', "'")):
            branch = t
        else:
            operands.append(t)
        i += 1
    return AsmInstruction(opcode, operands, store, branch, line)
