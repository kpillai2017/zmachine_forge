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

from zforge.compiler.i7.model import all_activities, ADJECTIVES, BUILTIN_KINDS, DICT_WORD, \
    TEXT_PROPERTIES, PhraseDef, strip_article, unquote
from zforge.compiler.i7.problems import Location
from zforge.compiler.i7.source import BodyLine
from zforge.compiler.i7.standard import (DIRECTIONS, PARSER_ERRORS, zil_name,
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


# Numbers written as words, as Inform allows: 'five minutes after T'.
NUMBER_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
NUMBER_WORDS.update({"thirty": 30, "forty": 40, "fifty": 50, "sixty": 60})


# Off-stage (ADR-059): a thing is off-stage when it is nowhere - in no room,
# carried by no one, in or on nothing. On-stage is the opposite.
STAGE = ("off-stage", "on-stage")


def stage_test(obj: str, adjective: str) -> str:
    """The test that OBJ is ADJECTIVE (off-stage or on-stage)."""
    return f"<NOT <LOC {obj}>>" if adjective == "off-stage" else f"<LOC {obj}>"


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


def definition_routine(adjective: str) -> str:
    """The routine that says whether something is ADJECTIVE (a 'Definition:')."""
    return "DEF-" + re.sub(r"[^A-Z0-9]+", "-", adjective.upper()).strip("-")


def entry_routine(column: str) -> str:
    """'reply' -> ENTRY-REPLY: prints the reply entry of the row a topic was found in."""
    return "ENTRY-" + re.sub(r"[^A-Z0-9]+", "-", column.upper()).strip("-")


TOPIC_LISTED = re.compile(r"^(?:a )?topic listed in (?:the )?(table .+)$", re.I)
ENTRY = re.compile(r"^(?:the )?(.+) entry$", re.I)


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
            "text" if kind == "text" else "time" if kind == "time" else "object"

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
        low = t.lower()
        if low in NUMBER_WORDS:                            # 'five minutes after T'
            return str(NUMBER_WORDS[low])
        m = re.fullmatch(r"(\d{1,2}):(\d\d) ?([ap])\.?m\.?", low)   # a time of day: minutes
        if m and int(m.group(1)) in range(1, 13) and int(m.group(2)) < 60:  # since midnight
            hours = int(m.group(1)) % 12 + (12 if m.group(3) == "p" else 0)
            return str(hours * 60 + int(m.group(2)))
        if low in ("midnight", "midday", "noon"):
            return "0" if low == "midnight" else "720"
        if low == "the time understood":                   # a [time] token's value
            return ",P-TIME"
        m = re.match(r"^(.+?) (minutes?|hours?) (after|before) (.+)$", t, re.I)
        if m:                                              # round the clock (1440 minutes)
            n = self.value(m.group(1), where)
            step = n if m.group(2).lower().startswith("minute") else f"<* {n} 60>"
            base = self.value(m.group(4), where)
            if m.group(3).lower() == "after":
                return f"<MOD <+ {base} {step}> 1440>"
            return f"<MOD <+ <- {base} <MOD {step} 1440>> 1440> 1440>"
        m = re.match(r"^(?:the )?holder of (.+)$", t, re.I)   # what it is in, on, part of
        if m:
            return f"<LOC {self.value(m.group(1), where)}>"
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
            known = (adjective in ADJECTIVES or adjective in self.L.m.either_or
                     or adjective in self.L.m.definitions or adjective in STAGE)
            if known and self.L.m.find(noun):
                article = m.group(1) or ""
                return (f"{article}{noun} {m.group(3)} {adjective} and "
                        f"{article}{noun} {m.group(3)} {m.group(4)}")
        return None

    def condition(self, text: str, where: Location) -> str:
        """Translate one Inform 7 condition into a ZIL test that returns true or false."""
        t = " ".join(text.strip().rstrip(",").split())
        # 'the topic understood matches "x" or "y"': before splitting at 'or',
        # which here joins the topic's phrases
        m = re.match(r'^the topic understood (does not |doesn\'t )?(match(?:es)?|include[s]?) '
                     r'(".*)$', t, re.I)
        if m:
            test = self.topic_test(m.group(3), m.group(2).lower().startswith("match"), where)
            return f"<NOT {test}>" if m.group(1) else test
        m = re.match(r"^the topic understood is (not )?(a topic listed in .+)$", t, re.I)
        if m:
            test = self.topic_test(m.group(2), True, where)
            return f"<NOT {test}>" if m.group(1) else test
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
        m = re.match(r"^in (.+)$", t, re.I)           # 'when in Forest3': the location
        if m:
            room = self.L.m.find(m.group(1))
            if room is not None and any(k.name == "room" for k in self.L.kind_chain(room)):
                return f"<EQUAL? ,HERE {self.value(m.group(1), where)}>"
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
        m = re.match(r"^(.+?) (does not |is not )?(?:is )?"
                     r"(carries|carry|carrying|wears|wear|wearing) (.+)$", t, re.I)
        if m and self.atom_of(m.group(1)):          # someone else (ADR-055)
            owner, obj = self.value(m.group(1), where), self.value(m.group(4), where)
            test = f"<IN? {obj} {owner}>"
            if m.group(3).lower().startswith("wear"):
                test = f"<AND {test} <FSET? {obj} ,WORNBIT>>"
            return f"<NOT {test}>" if m.group(2) else test
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
        m = re.match(r"^(.+?) (is|are) (not )?part of (.+)$", t, re.I)
        if m:                                         # a part: in its whole, as a part
            obj = self.value(m.group(1), where)
            test = f"<AND <IN? {obj} {self.value(m.group(4), where)}> <FSET? {obj} ,PARTBIT>>"
            return f"<NOT {test}>" if m.group(3) else test
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
        if adj in self.L.m.definitions:                 # defined by 'Definition:'
            return f"<{definition_routine(adj)} {self.value(subject, where)}>"
        if adj in STAGE:                                # 'the branches are off-stage'
            return stage_test(self.value(subject, where), adj)
        table = {**ADJECTIVES, **self.L.m.either_or}
        if adj in table:
            flag, value = table[adj]
            test = f"<FSET? {self.value(subject, where)} ,{flag}>"
            return test if value else f"<NOT {test}>"
        kind = strip_article(adj)
        if what.lower().startswith(("a ", "an ")):
            test = self.kind_test(self.value(subject, where), kind)
            if test is not None:
                return test
        if what.strip().startswith('"'):                 # 'the scent of it is "nothing"'
            return self.text_is(subject, what.strip(), where)
        return f"<EQUAL? {self.value(subject, where)} {self.value(what, where)}>"

    def text_is(self, subject: str, quoted: str, where: Location) -> str:
        """SUBJECT is the text QUOTED. A text value is a string (set by 'now') or,
        for a property's plain text, the one routine for its wording: either may
        match. (A text with substitutions is its own routine, equal only to itself.)"""
        try:
            parts = parse_text(quoted).parts
        except TextError as e:
            return self.problem(where, quoted, f"the text is malformed: {e}.")
        if not all(isinstance(p, Literal) for p in parts):
            return self.problem(where, quoted, "I7-lite can compare a text only with a text "
                                "without substitutions.")
        wording = "".join(p.text for p in parts)
        routine = self.L.plain_text(wording)
        values = [self.value(quoted, where)] + ([f",{routine}"] if routine else [])
        return f"<EQUAL? {self.value(subject, where)} {' '.join(values)}>"

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
        m = re.match(r"^doing (?:something|anything) to (.+)$", low)   # any action on it
        if m:
            noun = self.object_guard(",PRSO", text[len(text) - len(m.group(1)):], where)
            if noun:
                guards.insert(0, noun)
                spec[0] = 1
            return ActionPattern([], self.all_of(guards), tuple(spec))
        m = re.match(r"^doing (?:something|anything)(?: (?:other than|except) (.+))?$", low)
        if m:
            actions = []
            if m.group(1):
                found = self.excluded_actions(text[len(text) - len(m.group(1)):], where)
                if found is None:
                    return None
                excluded, noun = found
                verbs = " ".join(f",V?{self.L.action_atom[a]}" for a in excluded)
                guards.insert(0, f"<NOT <EQUAL? ,PRSA {verbs}>>")
                if noun:                            # '... or touching the ClearingLight'
                    test = self.object_guard(",PRSO", noun, where)
                    if test:
                        guards.insert(0, test)
                        spec[0] = 1
            return ActionPattern(actions, self.all_of(guards), tuple(spec))
        if low == "going nowhere":                  # no exit that way (room gone to is nothing)
            spec[0] = 1
            return ActionPattern(["going"], self.all_of(["<ZERO? ,GOING-TO>"] + guards),
                                 tuple(spec))
        actions, noun_guards, kind_guards = [], [], []
        alternatives = []
        for alt in split_outside_quotes(text, " or "):
            if alt.strip().startswith('"') and alternatives:   # 'about "roses" or "rose garden"':
                alternatives[-1] += " or " + alt              # one topic, not two actions
            else:
                alternatives.append(alt)
        for alt in alternatives:
            found = self.find_action(alt.strip(), where)
            if found is None:
                return None
            name, nouns = found
            actions.append(name)
            topic = None
            if self.L.m.actions[name].topic and len(nouns) == self.L.m.actions[name].applying:
                topic = nouns.pop()                 # the last slot is the topic, not a thing
            if nouns and alt is alternatives[-1]:
                noun_guards = self.noun_guards(nouns, where)
                kind_guards = self.broad_guards(nouns)
            if topic is not None and alt is alternatives[-1]:
                noun_guards.append(self.topic_guard(topic, where))
        spec[0] = len(noun_guards)                  # 'something' adds no specificity
        return ActionPattern(actions, self.all_of(noun_guards + kind_guards + guards),
                             tuple(spec))

    def excluded_actions(self, text: str, where: Location):
        """'examining or touching the ClearingLight' / 'examining or reading to
        the shadow' (after 'doing anything except' or 'other than'): the
        actions left out, and the thing the rule is about, if one is named -
        after the last action, or after 'to' (ADR-060). None after a problem."""
        alts = [a.strip() for a in text.split(" or ")]
        noun = None
        m = re.match(r"^(.+?) to (.+)$", alts[-1], re.I)
        if m and m.group(1).lower() in self.L.m.actions:   # not 'giving it to'
            alts[-1], noun = m.group(1), m.group(2)
        names = []
        for i, alt in enumerate(alts):
            found = self.find_action(alt, where)
            if found is None:
                return None
            names.append(found[0])
            if found[1] and i == len(alts) - 1 and noun is None:
                noun = found[1][0]
        return names, noun

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
                elif self.L.m.actions[name].topic:
                    # 'asking the Beast about', or just 'asking the Beast': any topic
                    m = (re.match(rf"^{re.escape(verb)} (.+?) {re.escape(preposition)}$", low)
                         or re.match(rf"^{re.escape(verb)} (.+)$", low))
                    if m:
                        nouns = [text[m.start(1):m.end(1)]]
            elif low == name:
                nouns = []
            elif low.startswith(name + " "):
                nouns = [text[len(name):].strip()]
            if nouns is not None and (best is None or len(name) > len(best[0])):
                best = (name, nouns)
        if best is None:              # 'Report timesetting:' - the verb of one 'X it Y' action
            named = [n for n in self.L.m.actions if " it " in n and n.split(" it ")[0] == low]
            if len(named) == 1:
                best = (named[0], [])
        if best is None:
            self.problem(where, text, "this is not an action I know (see docs/I7_LITE.md "
                         "for the standard actions, or define it with '... is an action "
                         "applying to ...').")
        return best

    def table_entry(self, words: str) -> str | None:
        """'reply entry' -> ENTRY-REPLY, if some topic table has that column."""
        m = ENTRY.match(words.strip())
        if m and any(m.group(1).lower() in t.columns and m.group(1).lower() != "topic"
                     for t in self.L.m.tables.values()):
            return entry_routine(m.group(1).lower())
        return None

    def topic_guard(self, topic: str, where: Location) -> str:
        """The test that the topic understood fits TOPIC, from a rule's preamble:
        'asking the Beast about "roses" or "rose garden"' - all of it, as in Inform."""
        return self.topic_test(topic, True, where)

    def topic_test(self, text: str, whole: bool, where: Location) -> str:
        """'"roses/rose/garden" or "rose garden"' -> a test of the topic understood.
        Each quoted phrase becomes a table for the parser's TOPIC-FITS?: a slash
        separates the words that may stand in one place, and '--' means none."""
        m = TOPIC_LISTED.match(text.strip())         # 'a topic listed in the Table of Notes'
        if m:
            table = self.L.m.tables.get(m.group(1).lower())
            if table is None:
                self.problem(where, text, f"there is no table called '{m.group(1)}'.")
                return "<RFALSE>"
            return f"<TABLE-{table.number}-FIND>"
        tests = []
        for phrase in split_outside_quotes(text, " or "):
            phrase = phrase.strip()
            if len(phrase) < 2 or not (phrase.startswith('"') and phrase.endswith('"')):
                self.problem(where, text, "a topic is written in quotation marks, like "
                             '"roses/rose garden" or "the Beast".')
                return "<RFALSE>"
            table = []
            for position in phrase[1:-1].lower().split():
                words = [w for w in position.split("/") if w]
                bad = [w for w in words if w != "--" and not DICT_WORD.match(w)]
                if bad or not words:
                    self.problem(where, text, f"'{position}' can't be a word of a topic "
                                 "(use letters, digits and hyphens).")
                    return "<RFALSE>"
                table += [str(len(words))] + ["0" if w == "--" else f",W?{w.upper()}"
                                              for w in words]
            if not table:
                self.problem(where, text, "a topic needs at least one word.")
                return "<RFALSE>"
            # The table goes right into the test (not in a global: a story has
            # only 240 of those, and Bronze alone has well over 100 topics).
            test = "TOPIC-MATCHES?" if whole else "TOPIC-INCLUDES?"
            tests.append(f"<{test} <TABLE {len(table)} {' '.join(table)}>>")
        return tests[0] if len(tests) == 1 else "<OR " + " ".join(tests) + ">"

    def noun_guards(self, nouns: list[str], where: Location) -> list[str]:
        guards = [self.object_guard(global_name, noun, where) for global_name, noun
                  in zip((",PRSO", ",PRSI")[:len(nouns)], nouns, strict=True)]
        return [g for g in guards if g]        # 'something' tests nothing (and adds no specificity)

    def broad_guards(self, nouns: list[str]) -> list[str]:
        """The kind tests for 'something' and 'someone' in a rule's preamble, which
        object_guard leaves out: 'something' is 'some thing', so Inform never
        matches it against a room or a direction (or no noun at all), and
        'someone' is a person (ADR-063). They add no specificity."""
        tests = []
        for global_name, noun in zip((",PRSO", ",PRSI")[:len(nouns)], nouns, strict=True):
            n = noun.strip().lower()
            if n in ("something", "anything", "a thing"):
                tests.append(f"<AND {global_name} <NOT <FSET? {global_name} ,ROOMBIT>> "
                             f"<NOT <GETP {global_name} ,P?DIR-PROP>>>")
            elif n == "someone":
                tests.append(f"<AND {global_name} <FSET? {global_name} ,PERSONBIT>>")
        return tests

    def object_guard(self, global_name: str, noun: str, where: Location) -> str:
        """The test that the object in GLOBAL_NAME fits NOUN, a description in a
        rule's preamble: 'something' (always: ""), 'a container' (a kind),
        'the lamp' (that one thing)."""
        n = noun.strip().lower()
        if n in ("something", "anything", "someone", "a thing"):
            return ""
        kind = strip_article(n)
        if n.startswith(("a ", "an ")):
            test = self.kind_test(global_name, kind)
            if test is not None:
                return test
        described = self.described(global_name, n, where)
        if described is not None:
            return described
        return f"<EQUAL? {global_name} {self.value(noun, where)}>"

    def adjective_test(self, global_name: str, adjective: str) -> str | None:
        """The test that the object in GLOBAL_NAME is ADJECTIVE, or None."""
        if adjective in self.L.m.definitions:
            return f"<{definition_routine(adjective)} {global_name}>"
        if adjective in STAGE:
            return stage_test(global_name, adjective)
        table = {**ADJECTIVES, **self.L.m.either_or}
        if adjective in table:
            flag, value = table[adjective]
            test = f"<FSET? {global_name} ,{flag}>"
            return test if value else f"<NOT {test}>"
        return None

    def described(self, global_name: str, n: str, where: Location) -> str | None:
        """'something scented', 'a scented thing', 'an open container': adjectives
        and a kind. None if N is not such a description (e.g. it names a thing)."""
        if self.L.m.find(n):
            return None
        words = n.split()
        if words and words[0] in ("something", "anything", "someone"):
            adjectives, kind = words[1:], ("person" if words[0] == "someone" else "thing")
        elif words and words[0] in ("a", "an") and len(words) > 2:
            adjectives, kind = words[1:-1], words[-1]
        else:
            return None
        tests, negate = [], False
        for a in adjectives:                      # 'an important not known tale'
            if a == "not":
                negate = True
                continue
            test = self.adjective_test(global_name, a)
            if test is None:
                return None
            tests.append(f"<NOT {test}>" if negate else test)
            negate = False
        if not tests or negate:
            return None
        if kind not in ("thing", "person"):
            test = self.kind_test(global_name, kind)
            if test is None:
                return None
            tests.append(test)
        return self.all_of(tests)

    def kind_test(self, operand: str, kind: str) -> str | None:
        """The test that OPERAND is of KIND, or None if KIND is no kind. A
        library kind has a flag; the author's kinds are tested by their members
        (kinds can't change in play), three at a time, as EQUAL? takes four."""
        if kind in KIND_FLAGS:
            return f"<FSET? {operand} ,{KIND_FLAGS[kind]}>"
        if kind not in self.L.m.kinds:
            return None
        members = [f",{self.L.atom[o.name]}" for o in self.L.m.objects.values()
                   if self.L.m.is_a(o.kind, kind)]
        if not members:
            return "<EQUAL? 0 1>"                      # a kind with nothing in it
        tests = [f"<EQUAL? {operand} {' '.join(members[i:i + 3])}>"
                 for i in range(0, len(members), 3)]
        return tests[0] if len(tests) == 1 else "<OR " + " ".join(tests) + ">"

    def activity_atom(self, name: str) -> str | None:
        """'the printing the banner text activity' -> PRINTING-BANNER-ACTIVITY"""
        n = name.strip().lower()
        n = n[4:] if n.startswith("the ") else n
        n = n[:-len(" activity")] if n.endswith(" activity") else n
        for activity in all_activities(self.L.m):
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
            comment = ph.preamble.replace('"', "'")   # a quotation mark would end the comment
            body = [f'<ROUTINE {name} ({locals_})   ;"{comment} (line {ph.where.line})"']
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
        # 'if X, <phrase>' comes first, so that in 'if X, say "..." instead'
        # the stopping belongs to the branch: it stops only when X holds.
        m = re.match(r"^if (.+?), (.+)$", t, re.I)             # if X, <phrase>
        if m and not t.endswith(":"):
            return [f"<COND ({self.condition(m.group(1), where)} "
                    f"{' '.join(self.phrase(m.group(2), where))})>"]
        # 'say "..." instead' / 'try looking instead': do it, then stop the action
        if low.endswith(" instead") and not low.startswith("instead"):
            return self.phrase(t[:-len(" instead")], where) + ["<RTRUE>"]
        if low.startswith("instead ") and len(low) > 8:   # 'instead say "..."' (ADR-055)
            return self.phrase(t[8:].strip(), where) + ["<RTRUE>"]
        if low.startswith("say "):
            return self.say(t[4:].strip(), where)
        likely = ("very unlikely", "unlikely", "possible", "likely", "very likely")
        if low.startswith("it is ") and low[6:] in likely:   # a 'Does the player mean'
            return [f"<RETURN {likely.index(low[6:]) + 1}>"]  # answer: its score, plus one
        if low in ("decide yes", "decide no", "yes", "no"):   # a 'To decide whether' (or
            return ["<RTRUE>" if low.endswith("yes") else "<RFALSE>"]   # definition's) answer
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
            return [f"<MOVE {obj} {dest}>" + self.unpart(obj)]
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
        if low in ("persuasion succeeds", "persuasion fails"):    # ADR-055
            return [f"<SETG PERSUADED {1 if low.endswith('succeeds') else 2}>", "<RTRUE>"]
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

    def unpart(self, obj: str) -> str:
        """A part moved anywhere else is no longer a part (only if the story has parts)."""
        return f" <FCLEAR {obj} ,PARTBIT>" if self.L.m.uses_parts else ""

    def now(self, text: str, where: Location) -> str:
        t = " ".join(text.split())
        m = re.match(r"^the player (carries|wears) (.+)$", t, re.I)
        if m:
            obj = self.value(m.group(2), where)
            if m.group(1).lower() == "wears":
                return f"<MOVE {obj} ,PLAYER> <FSET {obj} ,WORNBIT>" + self.unpart(obj)
            return f"<MOVE {obj} ,PLAYER>" + self.unpart(obj)
        m = re.match(r"^(.+?) (carries|wears) (.+)$", t, re.I)
        if m and self.atom_of(m.group(1)):            # someone else (ADR-055)
            owner, obj = self.value(m.group(1), where), self.value(m.group(3), where)
            flag = "FSET" if m.group(2).lower() == "wears" else "FCLEAR"
            return f"<MOVE {obj} {owner}> <{flag} {obj} ,WORNBIT>" + self.unpart(obj)
        m = re.match(r"^(.+?) (?:is|are) part of (.+)$", t, re.I)
        if m:                                         # a part: it goes with its whole
            obj = self.value(m.group(1), where)
            return f"<MOVE {obj} {self.value(m.group(2), where)}> <FSET {obj} ,PARTBIT>"
        m = re.match(r"^(.+?) (?:is|are) (off-stage|on-stage)$", t, re.I)
        if m:                                         # ADR-059
            if m.group(2).lower() == "on-stage":
                return self.problem(where, text, "'now ... is on-stage' does not say "
                                    "where it should be - use 'now ... is in ...'.")
            obj = self.value(m.group(1), where)
            return f"<REMOVE {obj}>" + self.unpart(obj)
        m = re.match(r"^(.+?) (?:is|are) (in|on) (.+)$", t, re.I)
        if m:
            obj = self.value(m.group(1), where)
            return f"<MOVE {obj} {self.value(m.group(3), where)}>" + self.unpart(obj)
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
                new = m.group(3).strip()             # a property's text is a routine
                value = (self.text_value(new, where)   # (a text variable's, a string)
                         if new.startswith('"') and target.startswith("<GETP ")
                         else self.value(new, where))
                return self.assign(target, value, where, text)
        return self.problem(where, text, "I7-lite cannot make this true with 'now'.")

    def text_value(self, quoted: str, where: Location) -> str:
        """A text as a value, to store: a routine that prints it, like a property's
        text (the same one for the same plain wording) - or 0 for "", no text."""
        if quoted == '""':
            return "0"
        try:
            text = parse_text(quoted)
        except TextError as e:
            return self.problem(where, quoted, f"the text is malformed: {e}.")
        before = len(self.L.routines)
        routine = self.L.text_routine("TEXT", text, f"a text set at line {where.line}",
                                      where, share=True)
        if len(self.L.routines) > before:               # a new routine: can it run later?
            used = [n for n, (local, _) in self.bindings.items()
                    if re.search(re.escape(local) + r"(?![\w?-])", self.L.routines[-1])]
            if used:
                self.L.routines.pop()
                return self.problem(where, quoted, f"this text uses '{used[0]}', a name that "
                                    "only exists while this rule runs, so it cannot be stored.")
        return f",{routine}"

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
        if self.table_entry(low):                         # say reply entry;
            return [f"<{self.table_entry(low)}>"]
        if low in ("line break", "paragraph break"):     # say line break;
            return [self.tell(parse_text(f"[{low}]"), sentence_break=False, where=where)]
        return [self.print_value(what, where)]

    def tell(self, text: Text, sentence_break: bool, where: Location | None = None) -> str:
        parts, owed = text.parts, False
        if sentence_break and parts and isinstance(parts[-1], Substitution) \
                and parts[-1].words.strip().lower() == "paragraph break":
            # A say that ends with a paragraph break, as Inform 7 prints it: a
            # line break, and a blank line owed - printed if more text follows,
            # but not before the prompt (which brings its own blank line).
            parts, owed = parts[:-1], True
        forms = self.parts(parts, where or Location(0))
        if owed:
            forms.append("<CRLF> <SETG SAY-P 0> <SETG PARA-BREAK 1>")
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
        said_phrase = False     # may a say phrase have just ended a line?
        for part in parts:
            if isinstance(part, Literal):
                if part.text:
                    # the line goes on after it: no longer at a line's end
                    out.append(("<SETG SAY-P 0> " if said_phrase else "")
                               + f"<TELL {zil_string(part.text)}>")
                    said_phrase = False
                continue
            if isinstance(part, Substitution):
                out.append(self.substitution(part.words, where))
            elif isinstance(part, IfText):
                clauses = []
                for cond, body in part.branches:
                    test = self.condition(cond, where) if cond else "ELSE"
                    # An empty branch does nothing: T, not <RFALSE>, which would
                    # leave the whole routine (ADR-059)
                    clauses.append(f"({test} {' '.join(self.parts(body, where)) or 'T'})")
                out.append("<COND " + " ".join(clauses) + ">")
            elif isinstance(part, OneOf):
                out.append(self.one_of(part, where))
            if any(f"<{r}>" in out[-1] for r in self.say_phrases.values()):
                said_phrase = True
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
        # An empty option prints nothing: T, not <RFALSE>, which would leave the
        # whole routine - the rest of the text and the rule's result (ADR-059).
        return " ".join(f"(<EQUAL? {index} {i}> {' '.join(self.parts(o, where)) or 'T'})"
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
                  "parser command so far": "<SAY-COMMAND-SO-FAR>",
                  "the topic understood": "<PRINT-TOPIC>", "topic understood": "<PRINT-TOPIC>"}
        if low in simple:
            return simple[low]
        if self.table_entry(low):                         # [reply entry]
            return f"<{self.table_entry(low)}>"
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
        named = m and self.kind_of_value(m.group(2)) == "object" and self.atom_of(m.group(2))
        if named or (m and m.group(2).lower().startswith("holder of ")):   # an object too
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
        if kind == "time":
            return f"<SAY-TIME {value}>"
        return f"<SAY-NAME {value}>"
