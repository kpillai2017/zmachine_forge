"""Quoted text: substitutions and Inform 7's printing conventions.

    "You see [the noun][if the cloak is worn], dimly[end if]."

becomes a small tree - Literal / Substitution / IfText / OneOf - that
lower.py turns into ZIL. Two Inform 7 conventions are applied here:

* a single quote ' prints as a double quote " unless it is inside a word
  (so 'don't' keeps its apostrophe, but 'Hello,' she said becomes "Hello,");
* text ending in . ! or ? (before the closing quote) ENDS A SENTENCE:
  when it is said, a line break follows (see ends_sentence)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Literal:
    text: str


@dataclass
class Substitution:
    words: str                                  # what was inside [ ]


@dataclass
class IfText:
    branches: list[tuple[str, list]]            # (condition, parts); "" = otherwise


@dataclass
class OneOf:
    options: list[list]
    mode: str                                   # "at random", "cycling", "stopping", ...


ONE_OF_MODES = ("purely at random", "at random", "cycling", "stopping",
                "in random order", "then at random")


@dataclass
class Text:
    parts: list = field(default_factory=list)
    raw: str = ""


class TextError(ValueError):
    """A malformed text (unbalanced brackets, [if] without [end if], ...)."""


def fix_quotes(s: str) -> str:
    """' -> " except between two letters (Inform 7's apostrophe rule)."""
    out = []
    for i, ch in enumerate(s):
        if ch == "'":
            before = s[i - 1] if i > 0 else " "
            after = s[i + 1] if i + 1 < len(s) else " "
            out.append("'" if before.isalpha() and after.isalpha() else '"')
        else:
            out.append(ch)
    return "".join(out)


def tokenize(body: str) -> list[tuple[str, str]]:
    """('lit', text) and ('sub', words) pieces."""
    pieces, i = [], 0
    while i < len(body):
        j = body.find("[", i)
        if j < 0:
            pieces.append(("lit", body[i:]))
            break
        if j > i:
            pieces.append(("lit", body[i:j]))
        k = body.find("]", j)
        if k < 0:
            raise TextError("a '[' has no matching ']'")
        pieces.append(("sub", " ".join(body[j + 1:k].split())))
        i = k + 1
    return [(kind, fix_quotes(t) if kind == "lit" else t) for kind, t in pieces]


def parse_text(quoted: str) -> Text:
    """'"..."' (with its quotes) -> Text."""
    body = quoted[1:-1] if quoted.startswith('"') and quoted.endswith('"') else quoted
    pieces = tokenize(body)
    parts, pos = _parse_parts(pieces, 0, stop=())
    if pos != len(pieces):
        raise TextError(f"unexpected [{pieces[pos][1]}]")
    return Text(parts, quoted)


def _parse_parts(pieces, pos, stop):
    parts = []
    while pos < len(pieces):
        kind, t = pieces[pos]
        low = t.lower()
        if kind == "sub" and (low in stop or any(low.startswith(s + " ") for s in stop
                                                 if s == "otherwise if")
                              or (low in ONE_OF_MODES and "or" in stop)):
            return parts, pos
        pos += 1
        if kind == "lit":
            parts.append(Literal(t))
        elif low.startswith("if "):
            branches, cond = [], t[3:]
            while True:
                body, pos = _parse_parts(pieces, pos, ("otherwise", "else", "otherwise if",
                                                       "end if", "end"))
                branches.append((cond, body))
                if pos >= len(pieces):
                    raise TextError(f"[if {t[3:]}] has no [end if]")
                nxt = pieces[pos][1].lower()
                pos += 1
                if nxt in ("end if", "end"):
                    break
                if nxt.startswith("otherwise if "):
                    cond = pieces[pos - 1][1][len("otherwise if "):]
                else:
                    cond = ""
            parts.append(IfText(branches))
        elif low == "one of":
            options = []
            while True:
                body, pos = _parse_parts(pieces, pos, ("or",))
                options.append(body)
                if pos >= len(pieces):
                    raise TextError("[one of] has no ending, e.g. [at random]")
                nxt = pieces[pos][1].lower()
                pos += 1
                if nxt != "or":
                    parts.append(OneOf(options, nxt))
                    break
        else:
            parts.append(Substitution(t))
    return parts, pos


def ends_sentence(text: Text) -> bool:
    """Inform 7: a said text ending in . ! or ? is followed by a line break -
    also when a closing bracket or quote follows the mark: Advent's
    '(Type ABOUT for details ...)' ends a sentence in the real game."""
    for part in reversed(text.parts):
        if isinstance(part, Literal):
            s = part.text.rstrip()
            if s:
                return s.rstrip(")]'\"")[-1:] in (".", "!", "?")
            continue
        return False                             # ends in a substitution
    return False
