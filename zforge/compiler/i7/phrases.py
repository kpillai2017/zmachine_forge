"""Lowering rule preambles, conditions, phrases and texts to ZIL-lite.

    Instead of going north in the Foyer when the cloak is worn:
        say "You can't leave yet.";
        increase the score by 1.

  preamble  'going north in the Foyer when the cloak is worn'
            -> rulebook: going / guard: PRSO is north, HERE is the Foyer, ...
  phrases   say -> <TELL ...>, increase -> <SETG ...>, if -> <COND ...>

Every function returns ZIL-lite source text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from zforge.compiler.i7.model import ADJECTIVES, BUILTIN_KINDS, PhraseDef, strip_article, unquote
from zforge.compiler.i7.problems import Location
from zforge.compiler.i7.source import BodyLine
from zforge.compiler.i7.standard import DIRECTIONS
from zforge.compiler.i7.text import IfText, Literal, OneOf, Substitution, Text, TextError, \
    ends_sentence, parse_text

if TYPE_CHECKING:
    from zforge.compiler.i7.lower import Lowerer

DIRECTION_NAMES = {name for name, _, _ in DIRECTIONS}
KIND_FLAGS = {k: flags[0] for k, (_, flags) in BUILTIN_KINDS.items() if flags and k != "room"}
COMPARISONS = [(" is less than ", "<L? {a} {b}>"), (" is greater than ", "<G? {a} {b}>"),
               (" is more than ", "<G? {a} {b}>"), (" is at least ", "<NOT <L? {a} {b}>>"),
               (" is at most ", "<NOT <G? {a} {b}>>"), (" < ", "<L? {a} {b}>"),
               (" > ", "<G? {a} {b}>"), (" >= ", "<NOT <L? {a} {b}>>"),
               (" <= ", "<NOT <G? {a} {b}>>")]


@dataclass
class ActionPattern:
    actions: list[str]                       # rulebooks to join ([] = every action)
    guard: str                               # ZIL condition, or ""
    specificity: tuple = (0, 0, 0)           # (noun tests, room test, when condition)


@dataclass
class Block:
    """A phrase and, for 'if ...:' lines, the phrases indented under it."""
    text: str
    where: Location
    children: list = field(default_factory=list)


def split_outside_quotes(text: str, sep: str) -> list[str]:
    parts, buf, in_quote = [], "", False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '"':
            in_quote = not in_quote
        if not in_quote and text.startswith(sep, i):
            parts.append(buf)
            buf, i = "", i + len(sep)
            continue
        buf += ch
        i += 1
    parts.append(buf)
    return parts


class PhraseLowerer:
    def __init__(self, lowerer: Lowerer):
        self.L = lowerer
        self.say_phrases: dict[str, str] = {}      # 'nokeys' -> routine
        self.decide_phrases: dict[str, str] = {}   # 'the cloak is hung' -> routine
        self.do_phrases: dict[str, str] = {}

    # ------------------------------------------------------------ helpers
    def problem(self, where: Location, wrote: str, why: str) -> str:
        self.L.p.problem(where, wrote, why)
        return "0"

    def atom_of(self, phrase: str) -> str | None:
        """The ZIL value an object/direction/variable name stands for."""
        p = strip_article(phrase).lower().strip()
        fixed = {"noun": ",PRSO", "second noun": ",PRSI", "player": ",PLAYER",
                 "yourself": ",PLAYER", "location": ",HERE", "score": ",SCORE",
                 "turn count": ",TURN-COUNT", "nothing": "0"}
        if p in fixed:
            return fixed[p]
        if p in DIRECTION_NAMES:
            return f",DIR-{p.upper()}"
        if p in self.L.var_atom:
            return f",{self.L.var_atom[p]}"
        obj = self.L.m.find(phrase)
        if obj:
            return f",{self.L.atom[obj.name]}"
        return None

    def kind_of_value(self, phrase: str) -> str:
        """'number', 'object' or 'text': how a value prints."""
        p = strip_article(phrase).lower().strip()
        if p in ("score", "turn count") or re.fullmatch(r"-?\d+", p):
            return "number"
        if p in self.L.m.variables:
            kind = self.L.m.variables[p].kind
            return "number" if kind in ("number", "truth state") else \
                "text" if kind == "text" else "object"
        return "object"

    # ------------------------------------------------------------ values
    def value(self, text: str, where: Location) -> str:
        t = text.strip()
        if re.fullmatch(r"-?\d+", t):
            return t
        if t.startswith('"'):
            return f'"{unquote(t)}"'
        if t.lower() in ("true", "false"):
            return "1" if t.lower() == "true" else "0"
        for word, op in ((" plus ", "+"), (" minus ", "-"), (" times ", "*"),
                         (" + ", "+"), (" - ", "-")):
            if word in t:
                a, b = t.rsplit(word, 1)
                return f"<{op} {self.value(a, where)} {self.value(b, where)}>"
        m = re.match(r"^(?:the )?(.+?) of (.+)$", t, re.I)
        if m and m.group(1).lower() in self.L.m.value_properties:
            obj = self.value(m.group(2), where)
            return f"<GETP {obj} ,P?{self.L.names_prop(m.group(1))}>"
        atom = self.atom_of(t)
        if atom is not None:
            return atom
        return self.problem(where, text, f"'{t}' is not a value, thing or room I know.")

    # ------------------------------------------------------------ conditions
    def condition(self, text: str, where: Location) -> str:
        t = " ".join(text.strip().rstrip(",").split())
        if len(ors := split_outside_quotes(t, " or ")) > 1:
            return "<OR " + " ".join(self.condition(x, where) for x in ors) + ">"
        if len(ands := split_outside_quotes(t, " and ")) > 1:
            return "<AND " + " ".join(self.condition(x, where) for x in ands) + ">"
        low = t.lower()
        for phrase, routine in self.decide_phrases.items():
            if low == phrase:
                return f"<{routine}>"
        if low in ("in darkness", "in the dark"):
            return "<NOT ,LIT>"
        m = re.match(r"^a random chance of (\d+) in (\d+) succeeds$", low)
        if m:
            return f"<NOT <G? <RANDOM {m.group(2)}> {m.group(1)}>>"
        m = re.match(r"^(?:the player|we) (?:is |are )?(not )?(?:in) (.+)$", t, re.I)
        if m:
            room = self.L.m.find(m.group(2))
            place = self.value(m.group(2), where)
            is_room = room is not None and self.L.m.is_a(room.kind, "room")
            test = f"<EQUAL? ,HERE {place}>" if is_room else f"<IN? ,PLAYER {place}>"
            return f"<NOT {test}>" if m.group(1) else test
        m = re.match(r"^the player (?:is )?(carries|carrying|wears|wearing) (.+)$", t, re.I)
        if m:
            obj = self.value(m.group(2), where)
            if m.group(1).lower().startswith("wear"):
                return f"<AND <IN? {obj} ,PLAYER> <FSET? {obj} ,WORNBIT>>"
            return f"<IN? {obj} ,PLAYER>"
        m = re.match(r"^(something|nothing) is (?:in|on) (.+)$", t, re.I)
        if m:
            test = f"<FIRST? {self.value(m.group(2), where)}>"
            return test if m.group(1).lower() == "something" else f"<NOT {test}>"
        for word, form in COMPARISONS:
            if word in t:
                a, b = t.split(word, 1)
                return form.format(a=self.value(a, where), b=self.value(b, where))
        m = re.match(r"^(.+?) (is|are) (not )?(in|on) (.+)$", t, re.I)
        if m:
            test = f"<IN? {self.value(m.group(1), where)} {self.value(m.group(5), where)}>"
            return f"<NOT {test}>" if m.group(3) else test
        m = re.match(r"^(.+?) (?:is|are) (not )?(.+)$", t, re.I)
        if m:
            subject, negated, what = m.group(1), bool(m.group(2)), m.group(3)
            test = self.is_test(subject, what, where, t)
            return f"<NOT {test}>" if negated else test
        return self.problem(where, text, "I7-lite does not understand this condition.")

    def is_test(self, subject: str, what: str, where: Location, whole: str) -> str:
        """'X is lit', 'X is a container', 'X is the Foyer', 'X is 3'."""
        adj = what.lower().strip()
        table = {**ADJECTIVES, **self.L.m.either_or}
        if adj in table:
            flag, value = table[adj]
            test = f"<FSET? {self.value(subject, where)} ,{flag}>"
            return test if value else f"<NOT {test}>"
        kind = strip_article(adj)
        if what.lower().startswith(("a ", "an ")) and kind in KIND_FLAGS:
            return f"<FSET? {self.value(subject, where)} ,{KIND_FLAGS[kind]}>"
        return f"<EQUAL? {self.value(subject, where)} {self.value(what, where)}>"

    # ------------------------------------------------------------ actions
    def action_pattern(self, preamble: str, where: Location) -> ActionPattern | None:
        text = " ".join(preamble.split())
        guards: list[str] = []
        spec = [0, 0, 0]
        parts = split_outside_quotes(text, " when ")
        if len(parts) > 1:
            text = parts[0]
            guards.append(self.condition(" when ".join(parts[1:]), where))
            spec[2] = 1
        # a trailing 'in <room>' limits the rule to that room
        m = re.match(r"^(.+) in (.+)$", text, re.I)
        if m:
            room = self.L.m.find(m.group(2))
            if room and self.L.m.is_a(room.kind, "room"):
                text = m.group(1)
                guards.insert(0, f"<EQUAL? ,HERE ,{self.L.atom[room.name]}>")
                spec[1] = 1
        low = text.lower()
        m = re.match(r"^doing (?:something|anything)(?: other than (.+))?$", low)
        if m:
            actions = []
            if m.group(1):
                excluded = [self.find_action(a.strip(), where) for a in m.group(1).split(" or ")]
                if None in excluded:
                    return None
                verbs = " ".join(f",V?{self.L.action_atom[a[0]]}" for a in excluded)
                guards.insert(0, f"<NOT <EQUAL? ,PRSA {verbs}>>")
            return ActionPattern(actions, self.all_of(guards), tuple(spec))
        actions, noun_guards = [], []
        alternatives = split_outside_quotes(text, " or ")
        for alt in alternatives:
            found = self.find_action(alt.strip(), where)
            if found is None:
                return None
            name, nouns = found
            actions.append(name)
            if nouns and alt is alternatives[-1]:
                noun_guards = self.noun_guards(nouns, where)
        spec[0] = len(noun_guards)
        return ActionPattern(actions, self.all_of(noun_guards + guards), tuple(spec))

    def find_action(self, text: str, where: Location):
        """'putting the cloak on the hook' -> ('putting it on', ['the cloak', 'the hook']).

        An action with 'it' in its name has two nouns around a preposition
        ('putting it on': putting X on Y); any other action is its name,
        then (if it applies to something) the noun. The longest name wins,
        so 'taking off the cloak' is 'taking off', not 'taking'."""
        low = text.lower()
        best: tuple[str, list[str]] | None = None
        for name in self.L.m.actions:
            nouns: list[str] | None = None
            if " it " in name:
                verb, preposition = name.split(" it ", 1)
                m = re.match(rf"^{re.escape(verb)} (.+?) {re.escape(preposition)} (.+)$", low)
                if m:
                    nouns = [text[m.start(1):m.end(1)], text[m.start(2):m.end(2)]]
            elif low == name:
                nouns = []
            elif low.startswith(name + " "):
                nouns = [text[len(name):].strip()]
            if nouns is not None and (best is None or len(name) > len(best[0])):
                best = (name, nouns)
        if best is None:
            self.problem(where, text, "this is not an action I know (see docs/I7_LITE.md "
                         "for the standard actions, or define it with '... is an action "
                         "applying to ...').")
        return best

    def noun_guards(self, nouns: list[str], where: Location) -> list[str]:
        out = []
        for global_name, noun in zip((",PRSO", ",PRSI")[:len(nouns)], nouns, strict=True):
            n = noun.strip().lower()
            if n in ("something", "anything", "someone", "a thing"):
                continue
            kind = strip_article(n)
            if n.startswith(("a ", "an ")) and kind in KIND_FLAGS:
                out.append(f"<FSET? {global_name} ,{KIND_FLAGS[kind]}>")
                continue
            out.append(f"<EQUAL? {global_name} {self.value(noun, where)}>")
        return out

    @staticmethod
    def all_of(guards: list[str]) -> str:
        guards = [g for g in guards if g]
        if not guards:
            return ""
        return guards[0] if len(guards) == 1 else "<AND " + " ".join(guards) + ">"

    # ------------------------------------------------------------ phrases
    def declare(self, phrases: list[PhraseDef]) -> None:
        """'To say nokeys:' / 'To decide whether the cloak is hung:' / 'To hang up:'"""
        self.defs = []
        for ph in phrases:
            head = ph.preamble[3:].strip()                   # after 'To '
            low = head.lower()
            if "(" in head:
                self.L.p.unsupported(ph.where, ph.preamble, "a phrase with parameters")
                continue
            if low.startswith("say "):
                name = self.L.names.new("SAY-" + head[4:])
                self.say_phrases[low[4:]] = name
            elif low.startswith("decide whether "):
                name = self.L.names.new("DECIDE-" + head[15:])
                self.decide_phrases[low[15:]] = name
            elif low.startswith("decide "):
                self.L.p.unsupported(ph.where, ph.preamble, "'To decide which/what' phrases")
                continue
            else:
                name = self.L.names.new("DO-" + head)
                self.do_phrases[low] = name
            self.defs.append((name, ph))
        for name, ph in self.defs:
            body = [f'<ROUTINE {name} ()   ;"{ph.preamble} (line {ph.where.line})"']
            body += ["    " + line for line in self.body(ph.body)]
            body.append("    <RFALSE>>")
            self.L.routines.append("\n".join(body))

    def body(self, lines: list[BodyLine]) -> list[str]:
        """Phrases (split at ';', nested by indentation) -> ZIL lines."""
        flat: list[Block] = []
        indents: list[int] = []
        for line in lines:
            pieces = [p.strip() for p in split_outside_quotes(line.text, ";") if p.strip()]
            for piece in pieces:
                flat.append(Block(piece, line.where))
                indents.append(line.indent)
        if flat and flat[-1].text.endswith("."):          # the rule's final full stop
            flat[-1].text = flat[-1].text[:-1].rstrip()   # ('say "Hi."' ends in a quote: kept)
        roots = self.nest(flat, indents)
        return self.blocks(roots)

    @staticmethod
    def nest(flat: list[Block], indents: list[int]) -> list[Block]:
        roots: list[Block] = []
        stack: list[tuple[int, Block]] = []
        for block, indent in zip(flat, indents, strict=True):
            while stack and indent <= stack[-1][0]:
                stack.pop()
            (stack[-1][1].children if stack else roots).append(block)
            if block.text.endswith(":"):
                stack.append((indent, block))
        return roots

    def blocks(self, blocks: list[Block]) -> list[str]:
        out: list[str] = []
        i = 0
        while i < len(blocks):
            b = blocks[i]
            low = b.text.lower()
            if low.startswith("if ") and b.text.endswith(":"):
                clauses = [(self.condition(b.text[3:-1], b.where), b.children)]
                while i + 1 < len(blocks):
                    nxt = blocks[i + 1]
                    nlow = nxt.text.lower()
                    if nlow.startswith(("otherwise if ", "else if ")) and nxt.text.endswith(":"):
                        cond = nxt.text.split(" if ", 1)[1][:-1]
                        clauses.append((self.condition(cond, nxt.where), nxt.children))
                    elif nlow in ("otherwise:", "else:"):
                        clauses.append(("ELSE", nxt.children))
                    else:
                        break
                    i += 1
                out.append("<COND " + " ".join(
                    f"({cond} {' '.join(self.blocks(kids)) or '<RFALSE>'})"
                    for cond, kids in clauses) + ">")
            else:
                out.extend(self.phrase(b.text, b.where))
            i += 1
        return out

    def phrase(self, text: str, where: Location) -> list[str]:
        t = text.strip()
        low = t.lower()
        # 'say "..." instead' / 'try looking instead': do it, then stop the action
        if low.endswith(" instead") and not low.startswith("instead"):
            return self.phrase(t[:-len(" instead")], where) + ["<RTRUE>"]
        m = re.match(r"^if (.+?), (.+)$", t, re.I)             # if X, <phrase>
        if m and not t.endswith(":"):
            return [f"<COND ({self.condition(m.group(1), where)} "
                    f"{' '.join(self.phrase(m.group(2), where))})>"]
        if low.startswith("say "):
            return self.say(t[4:].strip(), where)
        if low.startswith("now "):
            return [self.now(t[4:], where)]
        m = re.match(r"^(increase|decrease) (.+?) by (.+)$", t, re.I)
        if m:
            target, amount = self.value(m.group(2), where), self.value(m.group(3), where)
            op = "+" if m.group(1).lower() == "increase" else "-"
            return [f"<SETG {target[1:]} <{op} {target} {amount}>>"]
        m = re.match(r"^move (.+?) to (.+)$", t, re.I)
        if m:
            obj, dest = self.value(m.group(1), where), self.value(m.group(2), where)
            if obj == ",PLAYER":                              # the player goes somewhere
                return [f"<MOVE-PLAYER-TO {dest}>"]
            return [f"<MOVE {obj} {dest}>"]
        m = re.match(r"^remove (.+?) from play$", t, re.I)
        if m:
            return [f"<REMOVE {self.value(m.group(1), where)}>"]
        m = re.match(r'^end the story( finally)?(?: saying (".*"))?$', t, re.I)
        if m:
            code = [f"<SETG STORY-ENDED {2 if m.group(1) else 1}>"]
            if m.group(2):
                code.append(f'<SETG END-SAYING "{unquote(m.group(2))}">')
            return code + ["<RTRUE>"]
        if low in ("stop the action", "stop", "rule succeeds", "rule fails"):
            return ["<RTRUE>"]
        if low in ("continue the action", "make no decision"):
            return ["<RFALSE>"]
        m = re.match(r"^try (silently )?(.+)$", t, re.I)
        if m:
            return [self.try_action(m.group(2), bool(m.group(1)), where)]
        if low in self.do_phrases:
            return [f"<{self.do_phrases[low]}>"]
        self.problem(where, t, "I7-lite does not know this phrase.")
        return []

    def try_action(self, text: str, silently: bool, where: Location) -> str:
        found = self.find_action(text, where)
        if found is None:
            return ""
        name, nouns = found
        atom = self.L.action_atom[name]
        args = [self.value(n, where) for n in nouns] + ["0"] * (2 - len(nouns))
        if name == "going" and nouns:
            return f"<TRY ,V?GOING ,V-GOING {args[0]} 0{' 1' if silently else ''}>"
        return f"<TRY ,V?{atom} ,V-{atom} {args[0]} {args[1]}{' 1' if silently else ''}>"

    def now(self, text: str, where: Location) -> str:
        t = " ".join(text.split())
        m = re.match(r"^the player (carries|wears) (.+)$", t, re.I)
        if m:
            obj = self.value(m.group(2), where)
            if m.group(1).lower() == "wears":
                return f"<MOVE {obj} ,PLAYER> <FSET {obj} ,WORNBIT>"
            return f"<MOVE {obj} ,PLAYER>"
        m = re.match(r"^(.+?) (?:is|are) (in|on) (.+)$", t, re.I)
        if m:
            return f"<MOVE {self.value(m.group(1), where)} {self.value(m.group(3), where)}>"
        m = re.match(r"^(.+?) (?:is|are) (not )?(.+)$", t, re.I)
        if m:
            subject, negated, what = m.group(1), bool(m.group(2)), m.group(3).strip().lower()
            table = {**ADJECTIVES, **self.L.m.either_or}
            if what in table:
                flag, value = table[what]
                on = value != negated
                return f"<{'FSET' if on else 'FCLEAR'} {self.value(subject, where)} ,{flag}>"
            target = self.value(subject, where)
            if target.startswith(","):
                return f"<SETG {target[1:]} {self.value(m.group(3), where)}>"
        return self.problem(where, text, "I7-lite cannot make this true with 'now'.")

    # ------------------------------------------------------------ texts
    def say(self, what: str, where: Location) -> list[str]:
        if what.startswith('"'):
            try:
                return [self.tell(parse_text(what), sentence_break=True)]
            except TextError as e:
                return [self.problem(where, what, f"the text is malformed: {e}.")]
        low = what.lower()
        if low in self.say_phrases:
            return [f"<{self.say_phrases[low]}>"]
        return [self.print_value(what, where)]

    def tell(self, text: Text, sentence_break: bool) -> str:
        forms = self.parts(text.parts, Location(0))
        if sentence_break and ends_sentence(text):
            forms.append("<CRLF>")
        return " ".join(self.merge(forms)) or "<RTRUE>"

    @staticmethod
    def merge(forms: list[str]) -> list[str]:
        """Join neighbouring <TELL "..."> forms, for readable output."""
        out: list[str] = []
        for f in forms:
            if out and f.startswith('<TELL "') and out[-1].startswith('<TELL "') \
                    and out[-1].endswith('">') and f.endswith('">'):
                out[-1] = out[-1][:-2] + f[7:]
            else:
                out.append(f)
        return out

    def parts(self, parts: list, where: Location) -> list[str]:
        from zforge.compiler.i7.lower import zil_string
        out: list[str] = []
        for part in parts:
            if isinstance(part, Literal):
                if part.text:
                    out.append(f"<TELL {zil_string(part.text)}>")
            elif isinstance(part, Substitution):
                out.append(self.substitution(part.words, where))
            elif isinstance(part, IfText):
                clauses = []
                for cond, body in part.branches:
                    test = self.condition(cond, where) if cond else "ELSE"
                    clauses.append(f"({test} {' '.join(self.parts(body, where)) or '<RFALSE>'})")
                out.append("<COND " + " ".join(clauses) + ">")
            elif isinstance(part, OneOf):
                out.append(self.one_of(part, where))
        return out

    def one_of(self, part: OneOf, where: Location) -> str:
        n = len(part.options)
        mode = part.mode
        if mode in ("cycling", "stopping"):
            counter = self.L.names.new("ONE-OF")
            self.L.extra_globals.append(f"<GLOBAL {counter} 0>")
            step = (f"<SETG {counter} <MOD <+ ,{counter} 1> {n}>>" if mode == "cycling"
                    else f"<COND (<L? ,{counter} {n - 1}> <SETG {counter} <+ ,{counter} 1>>)>")
            branches = self.one_of_branches(f",{counter}", part.options, 0, where)
            return f"<COND {branches}> {step}"
        if mode not in ("at random", "purely at random", "in random order", "then at random"):
            return self.problem(where, f"[{mode}]", "this [one of] ending is not part of I7-lite.")
        roll = self.L.names.new("ROLL")
        self.L.extra_globals.append(f"<GLOBAL {roll} 0>")
        branches = self.one_of_branches(f",{roll}", part.options, 1, where)
        return f"<SETG {roll} <RANDOM {n}>> <COND {branches}>"

    def one_of_branches(self, index: str, options: list, first: int, where: Location) -> str:
        """(<EQUAL? index first> option-1) (<EQUAL? index first+1> option-2) ..."""
        return " ".join(f"(<EQUAL? {index} {i}> {' '.join(self.parts(o, where)) or '<RFALSE>'})"
                        for i, o in enumerate(options, start=first))

    def substitution(self, words: str, where: Location) -> str:
        w = words.strip()
        low = w.lower()
        simple = {"line break": "<CRLF>", "paragraph break": "<CRLF> <CRLF>",
                  "bold type": "<HLIGHT 2>", "italic type": "<HLIGHT 4>",
                  "roman type": "<HLIGHT 0>", "fixed letter spacing": "<HLIGHT 8>",
                  "variable letter spacing": "<HLIGHT 0>", "no line break": "",
                  "run paragraph on": "", "/b": "", "b": ""}
        if low in simple:
            return simple[low]
        if low in self.say_phrases:
            return f"<{self.say_phrases[low]}>"
        m = re.match(r"^(.+) in words$", w, re.I)
        if m:
            return f"<SAY-IN-WORDS {self.value(m.group(1), where)}>"
        m = re.match(r"^(the|The|a|A|an|An) (.+)$", w)
        if m and self.kind_of_value(m.group(2)) == "object" and self.atom_of(m.group(2)):
            article, target = m.group(1), self.value(m.group(2), where)
            routine = {"the": "SAY-THE", "The": "SAY-CAP-THE", "a": "SAY-A", "an": "SAY-A",
                       "A": "SAY-CAP-A", "An": "SAY-CAP-A"}[article]
            return f"<{routine} {target}>"
        return self.print_value(w, where)

    def print_value(self, what: str, where: Location) -> str:
        kind = self.kind_of_value(what)
        value = self.value(what, where)
        if kind == "number":
            return f"<TELL N {value}>"
        if kind == "text":
            return f"<PRINT {value}>"
        return f"<TELL D {value}>"
