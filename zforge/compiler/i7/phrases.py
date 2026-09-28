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

from zforge.compiler.i7.model import ADJECTIVES, BUILTIN_KINDS, TEXT_PROPERTIES, PhraseDef, \
    strip_article, unquote
from zforge.compiler.i7.problems import Location
from zforge.compiler.i7.source import BodyLine
from zforge.compiler.i7.standard import (ACTIVITIES, DIRECTIONS, PARSER_ERRORS, zil_name,
                                         zil_string)
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
    """Split text on separator, but not inside quoted strings."""
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


@dataclass
class ParamPhrase:
    """A phrase with parameters: how to find its uses, and its routine."""
    pattern: re.Pattern
    params: list[tuple[str, str, str]]      # (name, ZIL local, 'text'/'number'/'object')
    routine: str
    preamble: str


class PhraseLowerer:
    def __init__(self, lowerer: Lowerer):
        self.L = lowerer
        self.say_phrases: dict[str, str] = {}      # 'nokeys' -> routine
        self.decide_phrases: dict[str, str] = {}   # 'the cloak is hung' -> routine
        self.do_phrases: dict[str, str] = {}
        # phrases with parameters ('To pose the question (proposition - a text)
        # with affirmative response (hint text - a text):'), by use
        self.param_phrases: dict[str, list[ParamPhrase]] = {"do": [], "say": [], "decide": []}
        # while a phrase's body is compiled: its parameters, by name
        # ('hint text' -> ('.HINT-TEXT', 'text'))
        self.bindings: dict[str, tuple[str, str]] = {}
        self.aux: list[str] = []        # 'let' locals of the routine being compiled

    def take_aux(self) -> list[str]:
        """The 'let' locals made while compiling one routine's body; forgets
        them, and the names they were bound to, for the next routine."""
        aux, self.aux = self.aux, []
        self.bindings = {n: b for n, b in self.bindings.items() if b[0][1:] not in aux}
        return aux

    @staticmethod
    def locals_list(params: list[str], aux: list[str]) -> str:
        """Build ZIL locals list: parameter names, then AUX keyword, then aux local names."""
        return " ".join(params + (['"AUX"'] + aux if aux else []))

    # ------------------------------------------------------------ helpers
    def problem(self, where: Location, wrote: str, why: str) -> str:
        """Record an error message and return a safe fallback value (0)."""
        self.L.p.problem(where, wrote, why)
        return "0"

    def atom_of(self, phrase: str) -> str | None:
        """The ZIL value an object/direction/variable name stands for."""
        p = strip_article(phrase).lower().strip()
        if p in self.bindings and self.bindings[p][1] == "object":   # a phrase's parameter
            return self.bindings[p][0]
        fixed = {"noun": ",PRSO", "second noun": ",PRSI", "player": ",PLAYER",
                 "yourself": ",PLAYER", "location": ",HERE", "score": ",SCORE",
                 "turn count": ",TURN-COUNT", "nothing": "0",
                 # going's action variables (lib/i7/standard.zil GOING-VARIABLES)
                 "door gone through": ",GOING-DOOR", "room gone to": ",GOING-TO",
                 "room gone from": ",GOING-FROM"}
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
        if p in self.bindings:
            return self.bindings[p][1]
        if p in ("score", "turn count") or re.fullmatch(r"-?\d+", p):
            return "number"
        kind = None
        if p in self.L.m.variables:
            kind = self.L.m.variables[p].kind
        elif m := re.match(r"^(.+?) of (.+)$", p):          # the visit count of the Lab
            kind = self.L.m.value_properties.get(strip_article(m.group(1)))
        if kind is None:
            return "object"
        return "number" if kind in ("number", "truth state") else \
            "text" if kind == "text" else "object"

    # ------------------------------------------------------------ values
    def value(self, text: str, where: Location) -> str:
        t = text.strip()
        if strip_article(t).lower() in self.bindings:          # a phrase's parameter
            return self.bindings[strip_article(t).lower()][0]
        if re.fullmatch(r"-?\d+", t):
            return t
        if t.startswith('"'):
            return f'"{unquote(t)}"'
        if t.lower() in ("true", "false"):
            return "1" if t.lower() == "true" else "0"
        if t.lower() == "the item described":        # the object an activity is about
            return ",ACT-OBJ"
        if t.lower() == "the latest parser error":
            return ",LATEST-PARSER-ERROR"
        m = re.fullmatch(r"(?:the )?(.+) error", t, re.I)
        if m and m.group(1).lower() in PARSER_ERRORS:   # 'the can't see any such thing error'
            code = PARSER_ERRORS[m.group(1).lower()]
            return code if code.isdigit() else "," + code
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
    def described_subject(self, t: str) -> str | None:
        """A description as the subject: 'the locked grate is in the location'
        means the grate, if locked -> 'the grate is locked and the grate is in
        the location'. Only when 'locked grate' is not itself a name."""
        m = re.match(r"^(the |a |an )?([a-z][a-z -]*?) (is|are) (.+)$", t, re.I)
        if not m or self.L.m.find(m.group(2)):
            return None
        words = m.group(2).split()
        for n in range(1, len(words)):
            adjective, noun = " ".join(words[:n]).lower(), " ".join(words[n:])
            known = adjective in ADJECTIVES or adjective in self.L.m.either_or
            if known and self.L.m.find(noun):
                article = m.group(1) or ""
                return (f"{article}{noun} {m.group(3)} {adjective} and "
                        f"{article}{noun} {m.group(3)} {m.group(4)}")
        return None

    def condition(self, text: str, where: Location) -> str:
        """Translate one Inform 7 condition into a ZIL test that returns true or false."""
        t = " ".join(text.strip().rstrip(",").split())
        # Handle 'or': split and combine with <OR ...>
        if len(ors := split_outside_quotes(t, " or ")) > 1:
            return "<OR " + " ".join(self.condition(x, where) for x in ors) + ">"
        # Handle 'and': split and combine with <AND ...>
        if len(ands := split_outside_quotes(t, " and ")) > 1:
            return "<AND " + " ".join(self.condition(x, where) for x in ands) + ">"
        low = t.lower()
        # 'the locked grate is in the location' expands to two tests on 'the grate'
        described = self.described_subject(t)
        if described:                      # 'the locked grate is in the location'
            return self.condition(described, where)
        # A 'To decide whether' phrase that was defined
        for phrase, routine in self.decide_phrases.items():
            if low == phrase:
                return f"<{routine}>"
        # A 'To decide whether' phrase with parameters
        call = self.use_of("decide", t, where)
        if call:
            return call
        # Try special cases, then whereabouts, then general structure
        return (self.special_condition(t, low, where)
                or self.whereabouts_condition(t, where)
                or self.general_condition(t, where)
                or self.problem(where, text, "I7-lite does not understand this condition."))

    def special_condition(self, t: str, low: str, where: Location) -> str | None:
        """Conditions with a wording of their own: darkness, an activity going
        on, 'the player consents', an empty text, 'encloses', a random chance.
        None: not one of these (the next group is tried)."""
        if low in ("in darkness", "in the dark"):
            return "<NOT ,LIT>"
        # 'handling the X activity': test if activity is happening
        m = re.match(r"^handling (the .+ activity)$", t, re.I)
        if m:                                         # true if no for rule decided
            atom = self.activity_atom(m.group(1))
            if atom is None:
                return self.problem(where, t, f"'{m.group(1)}' is not an activity I7-lite knows.")
            return f"<HANDLING? ,{atom}>"
        if low == "the player consents":           # asks: yes or no?
            return "<YES?>"
        m = re.match(r'^(.+?) (is|is not) ""$', t, re.I)     # a text that is empty (or unset)
        if m:
            test = f"<ZERO? {self.value(m.group(1), where)}>"
            return test if m.group(2).lower() == "is" else f"<NOT {test}>"
        # 'X encloses Y' or 'X does not enclose Y'
        m = re.match(r"^(.+?) (does not enclose|encloses) (.+)$", t, re.I)
        if m:
            test = f"<ENCLOSES? {self.value(m.group(1), where)} {self.value(m.group(3), where)}>"
            return test if m.group(2).lower() == "encloses" else f"<NOT {test}>"
        # 'a random chance of N in M succeeds': succeed if random(M) <= N
        m = re.match(r"^a random chance of (\d+) in (\d+) succeeds$", low)
        if m:
            return f"<NOT <G? <RANDOM {m.group(2)}> {m.group(1)}>>"
        return None

    def whereabouts_condition(self, t: str, where: Location) -> str | None:
        """Where the player is and what they have: 'the player is in the Bar',
        'the player carries the lamp', 'the cloak is held', 'something is on
        the table'. None: not one of these."""
        m = re.match(r"^(?:the player|we) (?:is |are )?(not )?(?:in) (.+)$", t, re.I)
        if m:
            room = self.L.m.find(m.group(2))
            place = self.value(m.group(2), where)
            is_room = room is not None and self.L.m.is_a(room.kind, "room")
            test = f"<EQUAL? ,HERE {place}>" if is_room else f"<IN? ,PLAYER {place}>"
            return f"<NOT {test}>" if m.group(1) else test
        m = re.match(r"^the player (does not |is not )?(?:is )?"
                     r"(carries|carry|carrying|wears|wear|wearing) (.+)$", t, re.I)
        if m:
            obj = self.value(m.group(3), where)
            if m.group(2).lower().startswith("wear"):
                test = f"<AND <IN? {obj} ,PLAYER> <FSET? {obj} ,WORNBIT>>"
            else:
                test = f"<IN? {obj} ,PLAYER>"
            return f"<NOT {test}>" if m.group(1) else test
        m = re.match(r"^(.+?) (?:is|are) (not )?held$", t, re.I)    # held: carried or worn
        if m:
            test = f"<IN? {self.value(m.group(1), where)} ,PLAYER>"
            return f"<NOT {test}>" if m.group(2) else test
        m = re.match(r"^(something|nothing) is (?:in|on) (.+)$", t, re.I)
        if m:
            test = f"<FIRST? {self.value(m.group(2), where)}>"
            return test if m.group(1).lower() == "something" else f"<NOT {test}>"
        return None

    def general_condition(self, t: str, where: Location) -> str | None:
        """Comparisons ('the score is greater than 3'), 'X is in/on Y', and last
        'X is Y' in all its forms (is_test). None: not understood."""
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
        return None

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
        # 'in the presence of X': only while X is in the same room
        m = re.match(r"^(.+) in the presence of (.+)$", text, re.I)
        if m:
            text = m.group(1)
            guards.insert(0, f"<EQUAL? <LOC {self.value(m.group(2), where)}> ,HERE>")
            spec[1] = 1
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
        if low == "going nowhere":                  # no exit that way (room gone to is nothing)
            spec[0] = 1
            return ActionPattern(["going"], self.all_of(["<ZERO? ,GOING-TO>"] + guards),
                                 tuple(spec))
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
        guards = [self.object_guard(global_name, noun, where) for global_name, noun
                  in zip((",PRSO", ",PRSI")[:len(nouns)], nouns, strict=True)]
        return [g for g in guards if g]        # 'something' tests nothing (and adds no specificity)

    def object_guard(self, global_name: str, noun: str, where: Location) -> str:
        """The test that the object in GLOBAL_NAME fits NOUN, a description in a
        rule's preamble: 'something' (always: ""), 'a container' (a kind),
        'the lamp' (that one thing)."""
        n = noun.strip().lower()
        if n in ("something", "anything", "someone", "a thing"):
            return ""
        kind = strip_article(n)
        if n.startswith(("a ", "an ")) and kind in KIND_FLAGS:
            return f"<FSET? {global_name} ,{KIND_FLAGS[kind]}>"
        return f"<EQUAL? {global_name} {self.value(noun, where)}>"

    @staticmethod
    def activity_atom(name: str) -> str | None:
        """'the printing the banner text activity' -> PRINTING-BANNER-ACTIVITY"""
        n = name.strip().lower()
        n = n[4:] if n.startswith("the ") else n
        n = n[:-len(" activity")] if n.endswith(" activity") else n
        for activity in ACTIVITIES:
            if n == activity.name:
                return activity.atom
        return None

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
                self.declare_with_parameters(ph, head)
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
            params = next((pp.params for use in self.param_phrases.values() for pp in use
                           if pp.routine == name), [])
            self.bindings = {n: (f".{local}", kind) for n, local, kind in params}
            lines = self.body(ph.body)
            locals_ = self.locals_list([local for _, local, _ in params], self.take_aux())
            body = [f'<ROUTINE {name} ({locals_})   ;"{ph.preamble} (line {ph.where.line})"']
            body += ["    " + line for line in lines]
            body.append("    <RFALSE>>")
            self.bindings = {}
            self.L.routines.append("\n".join(body))

    def new_local(self, name: str, kind: str, aux: bool = False) -> str:
        """A new local for NAME (a loop variable, or with AUX a 'let' one)."""
        taken = {b[0][1:] for b in self.bindings.values()} | set(self.aux)
        local, n = zil_name(name), 2
        while local in taken:
            local, n = f"{zil_name(name)}-{n}", n + 1
        if aux:
            if len(self.aux) >= 12:                     # a routine has at most 15 locals
                raise ValueError("too many 'let' variables in one rule or phrase")
            self.aux.append(local)
        self.bindings[name] = (f".{local}", kind)
        return local

    def let(self, name: str, what: str, where: Location) -> str:
        """'let x be 3' / 'let the prize be the lamp' / 'let the reply be "Yes."'"""
        key = strip_article(name.strip()).lower()
        w = what.strip()
        kind = "text" if w.startswith('"') else self.kind_of_value(w)
        value = self.argument(w, kind, where)
        if key in self.bindings:                        # 'let' again: a new value
            return f"<SET {self.bindings[key][0][1:]} {value}>"
        try:
            local = self.new_local(key, kind, aux=True)
        except ValueError as e:
            return self.problem(where, f"let {name} be {what}", f"{e} (I7-lite allows 12).")
        return f"<SET {local} {value}>"

    PARAMETER = re.compile(r"\(\s*([^()]+?)\s+-\s+([^()]+?)\s*\)")

    def declare_with_parameters(self, ph: PhraseDef, head: str) -> None:
        """'pose the question (proposition - a text) with affirmative response
        (hint text - a text)' -> a routine with two locals, and a pattern that
        finds its uses: 'pose the question "..." with affirmative response "..."'."""
        use, words = "do", head
        if head.lower().startswith("say "):
            use, words = "say", head[4:]
        elif head.lower().startswith("decide whether "):
            use, words = "decide", head[15:]
        elif head.lower().startswith("decide "):
            self.L.p.unsupported(ph.where, ph.preamble, "'To decide which/what' phrases")
            return
        params, pattern, at = [], "", 0
        for m in self.PARAMETER.finditer(words):
            name, kind = m.group(1).lower(), self.parameter_kind(m.group(2))
            if kind is None:
                self.L.p.unsupported(ph.where, ph.preamble,
                                     f"a parameter of kind '{strip_article(m.group(2))}' "
                                     "(I7-lite's are "
                                     "texts, numbers, truth states and objects)")
                return
            pattern += self.literal_words(words[at:m.start()]) + "(.+?)"
            params.append((name, zil_name(name), kind))
            at = m.end()
        pattern += self.literal_words(words[at:])
        routine = self.L.names.new(f"{use.upper()}-" + self.PARAMETER.sub("X", words))
        self.param_phrases[use].append(ParamPhrase(re.compile(f"^{pattern}$", re.I),
                                                   params, routine, ph.preamble))
        self.defs.append((routine, ph))

    @staticmethod
    def literal_words(text: str) -> str:
        words = text.split()
        if not words:
            return r"\s*"
        return r"\s*" + r"\s+".join(re.escape(w) for w in words) + r"\s*"

    def parameter_kind(self, kind: str) -> str | None:
        k = strip_article(kind).lower().strip()
        if k == "text":
            return "text"
        if k in ("number", "truth state"):
            return "number"
        if k == "object" or k in BUILTIN_KINDS or k in self.L.m.kinds:
            return "object"
        return None

    def use_of(self, use: str, text: str, where: Location) -> str | None:
        """A use of a phrase with parameters -> the routine call, or None."""
        for pp in self.param_phrases[use]:
            m = pp.pattern.match(" ".join(text.split()))
            if not m:
                continue
            args = [self.argument(arg, kind, where)
                    for arg, (_, _, kind) in zip(m.groups(), pp.params, strict=True)]
            return f"<{pp.routine}" + "".join(" " + a for a in args) + ">"
        return None

    def argument(self, arg: str, kind: str, where: Location) -> str:
        a = arg.strip()
        if kind != "text":
            return self.value(a, where)
        bound = self.bindings.get(strip_article(a).lower())
        if bound and bound[1] == "text":                # a text passed on: already a routine
            return bound[0]
        if a.startswith('"'):
            try:
                text = parse_text(a)
            except TextError as e:
                return self.problem(where, a, f"the text is malformed: {e}.")
        else:                                           # a text variable: printed when used
            text = parse_text(f'"[{a}]"')
        routine = self.L.text_routine("TEXT-ARG", text,       # (no quotes in the comment)
                                      f"a text given to a phrase, line {where.line}", where)
        # The text is a routine of its own, so it cannot see this rule's or
        # phrase's locals. (Inform 7 would substitute it here and now.)
        used = [n for n, (local, _) in self.bindings.items()
                if re.search(re.escape(local) + r"(?![\w?-])", self.L.routines[-1])]
        if used:
            self.L.routines.pop()
            return self.problem(where, a, f"this text uses '{used[0]}', a name that only exists "
                                "inside this rule or phrase. I7-lite cannot pass such a text on "
                                "yet: say it here instead.")
        return "," + routine

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
        for i, b in enumerate(flat[:-1]):
            # 'if the player carries the rod,' with the phrase indented below it
            # is Inform 7's other way of writing 'if the player carries the rod:'
            if (b.text.endswith(",") and indents[i + 1] > indents[i]
                    and re.match(r"^(if|otherwise if|else if|unless|while) ", b.text, re.I)):
                b.text = b.text[:-1].rstrip() + ":"
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
            elif m := re.match(r"^repeat with (.+?) running from (.+?) to (.+?):$", b.text, re.I):
                name = m.group(1).lower()                 # a DO loop: its variable is a local
                start, end = self.value(m.group(2), b.where), self.value(m.group(3), b.where)
                local = self.new_local(name, "number")
                kids = " ".join(self.blocks(b.children))
                out.append(f"<DO ({local} {start} {end}) {kids}>")
            elif m := re.match(r"^while (.+):$", b.text, re.I):
                cond = self.condition(m.group(1), b.where)
                kids = " ".join(self.blocks(b.children))
                out.append(f"<REPEAT () <COND (<NOT {cond}> <RETURN>)> {kids}>")
            else:
                out.extend(self.phrase(b.text, b.where))
            i += 1
        return out

    def phrase(self, text: str, where: Location) -> list[str]:
        """Translate one Inform 7 phrase into zero or more ZIL-lite statements."""
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
        if low in ("decide yes", "decide no"):          # a 'To decide whether' answer
            return ["<RTRUE>" if low == "decide yes" else "<RFALSE>"]
        m = re.match(r"^let (.+?) be (.+)$", t, re.I)
        if m:
            return [self.let(m.group(1), m.group(2), where)]
        if low.startswith("now "):
            return [self.now(t[4:], where)]
        for group in (self.changing_phrase, self.steering_phrase):
            code = group(t, low, where)
            if code is not None:              # ([] is an answer too: 'do nothing')
                return code
        if low in self.do_phrases:
            return [f"<{self.do_phrases[low]}>"]
        call = self.use_of("do", t, where)
        if call:
            return [call]
        self.problem(where, t, "I7-lite does not know this phrase.")
        return []

    def changing_phrase(self, t: str, low: str, where: Location) -> list[str] | None:
        """Phrases that change a value or where something is: increase and
        decrease (increment, decrement), move, remove from play. None: not
        one of these."""
        m = re.match(r"^(increment|decrement) (.+)$", t, re.I)     # by one
        if m:
            verb = "increase" if m.group(1).lower() == "increment" else "decrease"
            t = f"{verb} {m.group(2)} by 1"
        m = re.match(r"^(increase|decrease) (.+?) by (.+)$", t, re.I)
        if m:
            target, amount = self.value(m.group(2), where), self.value(m.group(3), where)
            op = "+" if m.group(1).lower() == "increase" else "-"
            return [self.assign(target, f"<{op} {target} {amount}>", where, t)]
        m = re.match(r"^move (.+?) to (.+?)(, without printing a room description)?$", t, re.I)
        if m:
            obj, dest = self.value(m.group(1), where), self.value(m.group(2), where)
            if obj == ",PLAYER":        # Inform 7 describes the new room, unless told not to
                if m.group(3):
                    return [f"<MOVE-PLAYER-TO {dest}>"]
                return [f"<MOVE-PLAYER-TO {dest}>", "<DESCRIBE-ROOM>"]
            return [f"<MOVE {obj} {dest}>"]
        m = re.match(r"^remove (.+?) from play$", t, re.I)
        if m:
            return [f"<REMOVE {self.value(m.group(1), where)}>"]
        return None

    def steering_phrase(self, t: str, low: str, where: Location) -> list[str] | None:
        """Phrases that steer the story: ending it, stopping or continuing the
        action, beginning or ending an activity, trying another action.
        None: not one of these."""
        m = re.match(r'^end the story( finally)?(?: saying (".*"))?$', t, re.I)
        if m:
            code = [f"<SETG STORY-ENDED {2 if m.group(1) else 1}>"]
            if m.group(2):
                code.append(f'<SETG END-SAYING "{unquote(m.group(2))}">')
            return code + ["<RTRUE>"]
        if low in ("stop the action", "stop", "rule succeeds", "rule fails"):
            return ["<RTRUE>"]
        if low in ("continue the action", "continue the activity", "make no decision"):
            return ["<RFALSE>"]
        if low == "do nothing":                  # the rule applies, and says nothing
            return []
        m = re.match(r"^(begin|end|carry out) (the .+? activity)(?: with (.+))?$", t, re.I)
        if m:
            verb, atom = m.group(1).lower(), self.activity_atom(m.group(2))
            if atom is None:
                return [self.problem(where, t, f"'{m.group(2)}' is not an activity I7-lite knows.")]
            obj = self.value(m.group(3), where) if m.group(3) else "0"
            if verb == "begin":
                return [f"<BEGIN-ACTIVITY ,{atom} {obj}>"]
            if verb == "end":
                return [f"<END-ACTIVITY ,{atom}>"]
            return [f"<CARRY-OUT ,{atom} {obj} 0>"]
        # 'silently try taking the lamp' (Inform's order) or 'try silently taking the lamp'
        m = re.match(r"^(silently )?try (silently )?(.+)$", t, re.I)
        if m:
            return [self.try_action(m.group(3), bool(m.group(1) or m.group(2)), where)]
        return None

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
            if target.startswith((",", "<GETP ")):
                return self.assign(target, self.value(m.group(3), where), where, text)
        return self.problem(where, text, "I7-lite cannot make this true with 'now'.")

    def assign(self, target: str, new: str, where: Location, wrote: str) -> str:
        """Store into a variable (,X -> SETG) or a property (GETP -> PUTP)."""
        if target.startswith(","):
            return f"<SETG {target[1:]} {new}>"
        m = re.fullmatch(r"<GETP (.+) (,P\?[A-Z0-9-]+)>", target)
        if m:
            return f"<PUTP {m.group(1)} {m.group(2)} {new}>"
        return self.problem(where, wrote, "this is not a variable or property I can change.")

    # ------------------------------------------------------------ texts
    def say(self, what: str, where: Location) -> list[str]:
        if what.startswith('"'):
            try:
                return [self.tell(parse_text(what), sentence_break=True, where=where)]
            except TextError as e:
                return [self.problem(where, what, f"the text is malformed: {e}.")]
        low = what.lower()
        if low in self.say_phrases:
            return [f"<{self.say_phrases[low]}>"]
        if low in ("line break", "paragraph break"):     # say line break;
            return [self.tell(parse_text(f"[{low}]"), sentence_break=False, where=where)]
        return [self.print_value(what, where)]

    def tell(self, text: Text, sentence_break: bool, where: Location | None = None) -> str:
        forms = self.parts(text.parts, where or Location(0))
        if forms:                           # a blank line owed by an earlier rule
            forms.insert(0, "<PARA-FLUSH>")
        if sentence_break and ends_sentence(text):
            forms.append("<SENTENCE-BREAK>")
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
                  "run paragraph on": "", "/b": "", "b": "",
                  "bracket": '<TELL "[">', "close bracket": '<TELL "]">',  # [ and ] themselves
                  "parser command so far": "<SAY-COMMAND-SO-FAR>"}
        if low in simple:
            return simple[low]
        if low in self.say_phrases:
            return f"<{self.say_phrases[low]}>"
        call = self.use_of("say", w, where)
        if call:
            return call
        adaptive = self.adaptive(w, where)
        if adaptive:
            return adaptive
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

    # Adaptive text, fixed viewpoint (7c): the player is 'you', present tense.
    WE = {"We": "You", "we": "you", "us": "you", "Us": "You", "our": "your", "Our": "Your",
          "ourselves": "yourself", "Ourselves": "Yourself"}
    AGREEING = {"are": ("are", "is"), "Are": ("Are", "Is"), "'re": ("'re", "'s"),
                "have": ("have", "has"), "Have": ("Have", "Has"), "'ve": ("'ve", "'s")}
    PRONOUNS = {"They": ("You", "They", "It"), "they": ("you", "they", "it"),
                "them": ("you", "them", "it"), "Those": ("You", "Those", "That"),
                "those": ("you", "those", "that")}
    FIXED = {"here": "here", "Here": "Here", "now": "now", "Now": "Now", "'": "'"}
    # [can catch] [cannot carry] [might try]: a modal verb does not change
    # with its subject, so with a fixed viewpoint it is printed as written
    MODALS = r"(?:can|cannot|can't|could|couldn't|may|might|must|should|would|will|won't)"

    def adaptive(self, w: str, where: Location) -> str | None:
        """[We] [are] [regarding X] [They] and the story's own verbs ([flow])."""
        if w in self.WE:
            return f"<SAY-WE {zil_string(self.WE[w])}>"
        if w in self.AGREEING:
            return "<SAY-VERB {} {}>".format(*(zil_string(x) for x in self.AGREEING[w]))
        if w in self.PRONOUNS:
            return "<SAY-PRONOUN {} {} {}>".format(*(zil_string(x) for x in self.PRONOUNS[w]))
        if w in self.FIXED:
            return f"<TELL {zil_string(self.FIXED[w])}>"
        if w in ("It", "it", "There", "there"):
            # printed as written; what follows then agrees as a singular
            # ('[We] [are] crawling ... [There] [are] a dim light': 'There is')
            return f"<SAY-IT {zil_string(w)}>"
        if re.match(rf"^{self.MODALS}(?: [a-z]+)?$", w, re.I):
            return f"<TELL {zil_string(w)}>"
        if w.lower() in ("regarding it", "regarding nothing"):
            return "<SETG PRIOR-NAMED 0>"
        if w.lower() == "regarding them":            # what follows agrees as a plural
            return "<SETG PRIOR-NAMED ,SOME-THINGS>"
        m = re.match(r"^regarding (.+)$", w, re.I)
        if m:
            return f"<SETG PRIOR-NAMED {self.value(m.group(1), where)}>"
        forms = self.L.m.verbs.get(w.lower())
        if forms:                                   # To flow is a verb.  -> [flow]
            plural, singular = forms
            if w[:1].isupper():
                plural, singular = plural.capitalize(), singular.capitalize()
            return f"<SAY-VERB {zil_string(plural)} {zil_string(singular)}>"
        return None

    def print_value(self, what: str, where: Location) -> str:
        bound = self.bindings.get(strip_article(what.strip()).lower())
        if bound and bound[1] == "text":        # a text parameter is a routine: run it
            return f"<APPLY {bound[0]}>"
        m = re.match(r"^(?:the )?(.+?) of (.+)$", what.strip(), re.I)
        if m and (m.group(1).lower() in TEXT_PROPERTIES
                  or self.L.m.value_properties.get(m.group(1).lower()) == "text"):
            obj = self.value(m.group(2), where)   # a text property: string or routine
            return f"<SAY-TEXT {obj} ,P?{zil_name(m.group(1))}>"
        kind = self.kind_of_value(what)
        value = self.value(what, where)
        if kind == "number":
            return f"<TELL N {value}>"
        if kind == "text":
            return f"<PRINT {value}>"
        return f"<SAY-NAME {value}>"
