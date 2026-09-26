"""Stage 2 - the reader: tokens -> S-expressions (nested Forms and Lists).

This is the classic Lisp "reader". It knows nothing about what TELL or
ROUTINE mean; it only builds the tree:

    <ROUTINE GO () <TELL "Hi" CR>>
      -> Form[Atom ROUTINE, Atom GO, List[], Form[Atom TELL, Str "Hi", Atom CR]]
"""
from __future__ import annotations

from dataclasses import dataclass, field

from zforge.compiler.diagnostics import Diagnostics, Location
from zforge.compiler.lexer import Kind, Token


@dataclass
class Atom:
    name: str
    location: Location


@dataclass
class Number:
    value: int
    location: Location


@dataclass
class String:
    value: str
    location: Location


@dataclass
class LocalRef:           # .NAME
    name: str
    location: Location


@dataclass
class GlobalRef:          # ,NAME
    name: str
    location: Location


@dataclass
class Form:               # <head args...>   ("<>" has no items and means false)
    items: list = field(default_factory=list)
    location: Location = Location(0, 0)


@dataclass
class List:               # (items...)
    items: list = field(default_factory=list)
    location: Location = Location(0, 0)


def read(tokens: list[Token], diag: Diagnostics) -> list:
    """Read every top-level datum."""
    reader = _Reader(tokens, diag)
    out = []
    while reader.peek().kind != Kind.EOF:
        datum = reader.datum()
        if datum is not None:
            out.append(datum)
    return out


class _Reader:
    def __init__(self, tokens: list[Token], diag: Diagnostics):
        self.tokens = tokens
        self.i = 0
        self.diag = diag

    def peek(self) -> Token:
        return self.tokens[self.i]

    def next(self) -> Token:
        token = self.tokens[self.i]
        if token.kind != Kind.EOF:
            self.i += 1
        return token

    def datum(self):
        t = self.next()
        if t.kind == Kind.COMMENT:            # ; skips the next datum entirely
            if self.peek().kind != Kind.EOF:
                self.datum()
            return None
        if t.kind == Kind.LANGLE:
            return Form(self._items(Kind.RANGLE, t), t.location)
        if t.kind == Kind.LPAREN:
            return List(self._items(Kind.RPAREN, t), t.location)
        if t.kind in (Kind.RANGLE, Kind.RPAREN):
            self.diag.error(t.location, f"unexpected '{t.text}'")
            return None
        if t.kind == Kind.NUMBER:
            return Number(t.value, t.location)
        if t.kind == Kind.STRING:
            return String(t.value, t.location)
        if t.kind == Kind.LOCAL:
            return LocalRef(t.text.upper(), t.location)
        if t.kind == Kind.GLOBAL:
            return GlobalRef(t.text.upper(), t.location)
        return Atom(t.text, t.location)

    def _items(self, closer: Kind, opener: Token) -> list:
        items = []
        while True:
            t = self.peek()
            if t.kind == closer:
                self.next()
                return items
            if t.kind == Kind.EOF:
                if not self.diag:             # don't pile onto a lexer error
                    self.diag.error(opener.location, f"'{opener.text}' is never closed")
                return items
            if t.kind in (Kind.RANGLE, Kind.RPAREN):
                self.next()
                self.diag.error(t.location, f"expected '{closer.value}' but found '{t.text}'")
                return items
            datum = self.datum()
            if datum is not None:
                items.append(datum)
