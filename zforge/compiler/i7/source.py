"""Reading I7 source: comments, headings, sentences and rule bodies.

Inform 7 source is prose. This module only finds where each sentence
starts and ends; what a sentence MEANS is model.py's job.

* [Square brackets] outside quoted text are comments (they may span lines).
* A sentence ends with '.' outside quotes, or with a quoted text whose
  last character is . ! or ? ("You are standing here." ends a sentence).
* A RULE is a preamble ending in ':' followed by phrases: on the same
  line separated by ';', or on the following indented lines. The rule
  ends at a blank line (or at the next unindented line). A one-line rule
  may use a comma instead: 'Instead of taking the lamp, say "No."'.
* Headings (Volume/Book/Part/Chapter/Section ...) are skipped."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from zforge.compiler.i7.problems import Location

# Patterns for the three kinds of line that are not ordinary assertions:
# headings (skipped), the title line, and the first words of a rule.
HEADING = re.compile(r"^(volume|book|part|chapter|section)\b", re.IGNORECASE)
TITLE = re.compile(r'^"[^"]+"(\s+by\s+.+)?\.?$')
RULE_START = re.compile(
    r"^((the |a )?(first|last) )?"                  # 'The first after ... rule:'
    r"(when play begins|when play ends|every turn|instead of|before|after|check|"
    r"carry out|report|rule for |to |this is the )", re.IGNORECASE)


@dataclass
class BodyLine:
    """One phrase line of a rule body; indent counts tab stops."""
    text: str
    where: Location
    indent: int


@dataclass
class Sentence:
    """One sentence or rule from the source, with optional indented rule body lines."""
    text: str
    where: Location
    body: list[BodyLine] = field(default_factory=list)   # rules only

    @property
    def is_rule(self) -> bool:
        return bool(self.body) or self.text.rstrip().endswith(":")


def strip_comments(text: str) -> str:
    """Blank out [comments] outside quoted text, keeping every newline so
    line numbers stay right. Brackets INSIDE quotes are substitutions."""
    # Walk the text one character at a time. DEPTH counts how many [comment
    # brackets] are open (comments can nest); a quote only counts when we
    # are not inside a comment.
    out, depth, in_quote = [], 0, False
    for ch in text:
        if depth == 0 and ch == '"':
            in_quote = not in_quote
        if not in_quote and ch == "[":
            depth += 1
        if depth:
            out.append("\n" if ch == "\n" else " ")
        else:
            out.append(ch)
        if not in_quote and ch == "]" and depth:
            depth -= 1
    return "".join(out)


def indent_of(line: str) -> int:
    """Tabs count one each; four spaces count as one tab."""
    tabs = spaces = 0
    for ch in line:
        if ch == "\t":
            tabs += 1
        elif ch == " ":
            spaces += 1
        else:
            break
    return tabs + spaces // 4


def colon_outside_quotes(text: str) -> int:
    """Index of the first ':' outside quotes, or -1."""
    in_quote = False
    for i, ch in enumerate(text):
        if ch == '"':
            in_quote = not in_quote
        elif ch == ":" and not in_quote:
            return i
    return -1


def comma_outside_quotes(text: str) -> int:
    """Index of the first ',' outside quotes, or -1."""
    in_quote = False
    for i, ch in enumerate(text):
        if ch == '"':
            in_quote = not in_quote
        elif ch == "," and not in_quote:
            return i
    return -1


def split_sentences(text: str, where: Location) -> list[Sentence]:
    """Split one run of assertion text into sentences."""
    # BUF collects the current sentence; START remembers where it began so
    # problem messages can name the right line and column.
    out, buf, start, in_quote = [], "", None, False
    line, col = where.line, where.column
    for i, ch in enumerate(text):
        if start is None and not ch.isspace():
            start = Location(line, col)
        buf += ch
        if ch == '"':
            in_quote = not in_quote
            # A closing quote ends the sentence if the text inside ended with . ! or ?
            # and a space (or the end) follows: 'The Hall is a room. "Dark." It ...'
            ends = (not in_quote and len(buf) >= 2 and buf[-2] in ".!?"
                    and (i + 1 == len(text) or text[i + 1].isspace()))
        else:
            ends = ch == "." and not in_quote
        if ends and buf.strip():
            out.append(Sentence(buf.strip(), start or where))
            buf, start = "", None
        # Keep track of line and column as we go.
        if ch == "\n":
            line, col = line + 1, 1
        else:
            col += 1
    # Whatever is left at the end (a last sentence without a full stop).
    if buf.strip():
        out.append(Sentence(buf.strip(), start or where))
    return out


def is_continuation(line: str) -> bool:
    """A preamble too long for one line goes on in lines that start with a
    space or three (Inform 7's way; a body line is indented a tab or 4 spaces):
        To pose the question (proposition - a text)
         with affirmative response (hint text - a text):"""
    return line.startswith(" ") and bool(line.strip()) and indent_of(line) == 0


def join_continuations(lines: list[str], i: int, text: str) -> tuple[str, int]:
    """TEXT (line I) with the continuation lines after it; and the next line."""
    j = i + 1
    while j < len(lines) and is_continuation(lines[j]):
        text += " " + lines[j].strip()
        j += 1
    return text, j


def read_sentences(source: str) -> list[Sentence]:
    """The whole source as sentences, in order; rules carry their bodies."""
    lines = strip_comments(source).replace("\r\n", "\n").split("\n")
    out: list[Sentence] = []
    i = 0
    # The first line, if it is quoted ("Title" by Author), is the titling
    # sentence by itself - it needs no full stop and no blank line after it.
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and TITLE.match(lines[i].strip()):
        out.append(Sentence(lines[i].strip().rstrip("."), Location(i + 1, 1)))
        i += 1
    # Every other line starts one of three things: a rule written with a colon,
    # a one-line rule written with a comma, or a paragraph of assertions.
    while i < len(lines):
        raw = lines[i]
        text = raw.strip()
        if not text or HEADING.match(text):
            i += 1
            continue
        where = Location(i + 1, len(raw) - len(raw.lstrip()) + 1)
        colon = colon_outside_quotes(text)
        comma = comma_outside_quotes(text)
        body_from = i + 1
        if RULE_START.match(text) and (
                colon < 0 and (comma < 0 or text.lower().startswith("to "))
                or comma >= 0 and colon < 0 and not text[comma + 1:].strip()):
            # the preamble (or a one-line rule's phrase) goes on in the next lines
            text, body_from = join_continuations(lines, i, text)
            colon, comma = colon_outside_quotes(text), comma_outside_quotes(text)
        # A rule with a colon: its phrases follow on this line and/or the
        # indented lines below.
        if RULE_START.match(text) and colon >= 0:
            i = read_rule(lines, i, text, colon, where, out, body_from)
            continue
        if RULE_START.match(text) and comma >= 0 and not text.lower().startswith("to "):
            # a one-line rule: 'Instead of taking the lamp, say "No."'
            i = read_rule(lines, i, text, comma, where, out, body_from)
            continue
        # an assertion paragraph: gather lines up to a blank line or a rule
        chunk, first = [raw], i
        i += 1
        while i < len(lines) and lines[i].strip() and not RULE_START.match(lines[i].strip()):
            chunk.append(lines[i])
            i += 1
        for s in split_sentences("\n".join(chunk), Location(first + 1, 1)):
            # A one-line rule can follow another sentence on the same line, as
            # in Inform: 'The count is a number that varies. Every turn:
            # increase the count by 1.' It is read as a rule on a line of its own.
            colon, comma = colon_outside_quotes(s.text), comma_outside_quotes(s.text)
            if RULE_START.match(s.text) and colon >= 0:
                read_rule([s.text], 0, s.text, colon, s.where, out, 1)
            elif RULE_START.match(s.text) and comma >= 0 and not s.text.lower().startswith("to "):
                read_rule([s.text], 0, s.text, comma, s.where, out, 1)
            else:
                out.append(s)
    return out


def read_rule(lines: list[str], i: int, text: str, colon: int,
              where: Location, out: list[Sentence], body_from: int | None = None) -> int:
    """A rule: 'preamble: phrase; phrase.' and/or indented lines after it.
    BODY_FROM: the first line after the preamble (it may take several)."""
    # The part before the colon names the rule; anything after it on the same
    # line is the first phrase of the body.
    preamble = text[:colon].strip()
    rest = text[colon + 1:].strip()
    rule = Sentence(preamble + ":", where)
    base = indent_of(lines[i])
    if rest:
        rule.body.append(BodyLine(rest, Location(where.line, where.column + colon + 1),
                                  base + 1))
    i = body_from if body_from is not None else i + 1
    # The body goes on while lines are indented deeper than the rule itself;
    # a blank line or a line back at the rule's own indent ends it.
    while i < len(lines) and lines[i].strip() and indent_of(lines[i]) > base:
        raw = lines[i]
        rule.body.append(BodyLine(raw.strip(), Location(i + 1, len(raw) - len(raw.lstrip()) + 1),
                                  indent_of(raw)))
        i += 1
    out.append(rule)
    return i
