"""Stage 1 - the lexer: characters -> tokens.

ZIL's surface syntax is small (it is MDL, a Lisp):

    <  >        a FORM: a call, e.g. <TELL "Hi" CR>        ("<>" is false)
    (  )        a LIST: argument lists, property definitions
    "..."       a string; \\" escapes a quote, | means newline
    123  -5     decimal numbers
    .NAME       the value of a LOCAL variable
    ,NAME       the value of a GLOBAL (also constants, objects, routines)
    NAME        an ATOM (form names, bare words like CR, TO, ELSE)
    ;           comments out the NEXT expression, e.g. ;"a comment"
    !\\c         a character literal (value = its ZSCII code)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from zforge.compiler.diagnostics import Diagnostics, Location

ATOM_BREAK = set(" \t\r\n<>()\";,")


class Kind(Enum):
    LANGLE = "<"
    RANGLE = ">"
    LPAREN = "("
    RPAREN = ")"
    STRING = "string"
    NUMBER = "number"
    ATOM = "atom"
    LOCAL = "local"        # .NAME
    GLOBAL = "global"      # ,NAME
    COMMENT = ";"          # comments out the next datum (the reader handles it)
    EOF = "eof"


@dataclass
class Token:
    kind: Kind
    text: str
    location: Location
    value: object = None


class Lexer:
    def __init__(self, source: str, diagnostics: Diagnostics):
        self.src = source
        self.diag = diagnostics
        self.pos = 0
        self.line = 1
        self.column = 1

    def _advance(self) -> str:
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _peek(self, offset: int = 0) -> str:
        i = self.pos + offset
        return self.src[i] if i < len(self.src) else ""

    def tokens(self) -> list[Token]:
        out: list[Token] = []
        while True:
            while self._peek() and self._peek().isspace():
                self._advance()
            loc = Location(self.line, self.column)
            ch = self._peek()
            if not ch:
                out.append(Token(Kind.EOF, "", loc))
                return out
            if ch in "<>()":
                self._advance()
                out.append(Token(Kind(ch), ch, loc))
            elif ch == ";":
                self._advance()
                out.append(Token(Kind.COMMENT, ";", loc))
            elif ch == '"':
                token = self._string(loc)
                if token is None:            # unterminated: nothing more can be trusted
                    out.append(Token(Kind.EOF, "", loc))
                    return out
                out.append(token)
            elif ch == "!" and self._peek(1) == "\\":
                self._advance(), self._advance()
                c = self._advance() if self._peek() else " "
                out.append(Token(Kind.NUMBER, "!\\" + c, loc, ord(c)))
            elif ch in ".," and self._peek(1) and self._peek(1) not in ATOM_BREAK:
                self._advance()
                name = self._atom_text()
                out.append(Token(Kind.LOCAL if ch == "." else Kind.GLOBAL, name, loc))
            else:
                text = self._atom_text()
                if not text:                  # a stray character
                    self._advance()
                    self.diag.error(loc, f"unexpected character {ch!r}")
                    continue
                if _is_number(text):
                    out.append(Token(Kind.NUMBER, text, loc, int(text)))
                else:
                    out.append(Token(Kind.ATOM, text.upper(), loc))

    def _atom_text(self) -> str:
        start = self.pos
        while self._peek() and self._peek() not in ATOM_BREAK:
            if self._peek() == "\\":
                self._advance()               # \x quotes one character in an atom
            self._advance()
        return self.src[start:self.pos]

    def _string(self, loc: Location) -> Token | None:
        self._advance()                        # opening quote
        chars: list[str] = []
        while True:
            ch = self._peek()
            if not ch:
                self.diag.error(loc, "unterminated string (missing closing \")")
                return None
            self._advance()
            if ch == '"':
                break
            if ch == "\\" and self._peek():
                chars.append(self._advance())
            elif ch == "|":
                chars.append("\n")             # ZIL: | is a line break
                if self._peek() == "\n":
                    self._advance()            # "|<newline>" is ONE line break
            elif ch == "\n":
                chars.append(" ")              # real newlines become spaces...
                while self._peek() in (" ", "\t"):
                    self._advance()            # ...and indentation is dropped
            else:
                chars.append(ch)
        return Token(Kind.STRING, "".join(chars), loc, "".join(chars))


def _is_number(text: str) -> bool:
    body = text[1:] if text[:1] in "-+" and len(text) > 1 else text
    return body.isdigit()
