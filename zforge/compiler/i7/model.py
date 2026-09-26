"""The world model: what an I7-lite source asserts about its world.

Built in two passes over the sentences (so forward references work):
  1. names    - every room, thing, kind, variable and action the source
                creates, so 'The Bar is south of the Foyer' can mention
                the Bar before the sentence that describes it;
  2. meaning  - placement, map, properties, rules, grammar.

Nothing here knows about ZIL: lower.py turns this model into code."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from zforge.compiler.i7.problems import Location, Problems
from zforge.compiler.i7.source import BodyLine, Sentence
from zforge.compiler.i7.standard import ACTIONS, DIRECTIONS, OPPOSITE, StandardAction
from zforge.compiler.i7.text import Text, TextError, parse_text

ARTICLES = ("the ", "a ", "an ", "some ")
DIRECTION_NAMES = {name for name, _, _ in DIRECTIONS}

# either/or properties the library understands: adjective -> (flag, value)
ADJECTIVES = {
    "lit": ("LITBIT", True), "dark": ("LITBIT", False),
    "scenery": ("SCENERYBIT", True), "fixed in place": ("FIXEDBIT", True),
    "portable": ("FIXEDBIT", False),
    "open": ("OPENBIT", True), "closed": ("OPENBIT", False),
    "openable": ("OPENABLEBIT", True), "unopenable": ("OPENABLEBIT", False),
    "locked": ("LOCKEDBIT", True), "unlocked": ("LOCKEDBIT", False),
    "lockable": ("LOCKABLEBIT", True),
    "wearable": ("WEARABLEBIT", True), "edible": ("EDIBLEBIT", True),
    "worn": ("WORNBIT", True),
    "switched on": ("ONBIT", True), "switched off": ("ONBIT", False),
    "proper-named": ("PROPERBIT", True), "improper-named": ("PROPERBIT", False),
    "plural-named": ("PLURALBIT", True), "singular-named": ("PLURALBIT", False),
    "visited": ("VISITEDBIT", True), "handled": ("HANDLEDBIT", True),
}
# built-in kinds: name -> (parent, flags every object of the kind gets)
BUILTIN_KINDS = {
    "object": (None, ()), "room": ("object", ("ROOMBIT", "LITBIT")),
    "thing": ("object", ()), "container": ("thing", ("CONTAINERBIT",)),
    "supporter": ("thing", ("SUPPORTERBIT",)), "door": ("thing", ("DOORBIT", "FIXEDBIT")),
    "device": ("thing", ("DEVICEBIT",)), "person": ("thing", ("PERSONBIT",)),
    "man": ("person", ()), "woman": ("person", ()), "animal": ("person", ()),
}
TEXT_PROPERTIES = {"description": "DESCRIPTION", "initial appearance": "INITIAL-APPEARANCE",
                   "printed name": "PRINTED-NAME"}


@dataclass
class Kind:
    name: str
    parent: str | None
    flags: set[str] = field(default_factory=set)            # set on every instance
    unflags: set[str] = field(default_factory=set)          # cleared on every instance
    where: Location = Location(0)


@dataclass
class Obj:
    name: str                                               # "small brass hook"
    kind: str
    where: Location
    parent: str | None = None                               # name of room/container
    relation: str = "in"                                    # in / on / carried / worn
    flags: set[str] = field(default_factory=set)
    unflags: set[str] = field(default_factory=set)
    texts: dict[str, Text] = field(default_factory=dict)    # description, ...
    values: dict[str, str] = field(default_factory=dict)    # value properties
    words: list[str] = field(default_factory=list)          # extra Understand words
    proper: bool = False


@dataclass
class Variable:
    name: str
    kind: str                                               # number / truth state / text / object
    initial: str = "0"
    where: Location = Location(0)


@dataclass
class Action:
    name: str
    applying: int
    standard: StandardAction | None = None
    out_of_world: bool = False
    grammar: list[tuple[str, Location]] = field(default_factory=list)


@dataclass
class Rule:
    stage: str                  # "when play begins", "every turn", or a STAGES name
    preamble: str               # what follows the stage words, e.g. "going north in the Foyer"
    body: list[BodyLine]
    where: Location
    number: int = 0


@dataclass
class PhraseDef:
    preamble: str               # "To say foo", "To decide whether ..."
    body: list[BodyLine]
    where: Location


@dataclass
class WorldModel:
    title: str = "Untitled"
    author: str = "Anonymous"
    headline: str = "An Interactive Fiction"
    release: int = 1
    scoring: bool = False
    max_score: int = 0
    kinds: dict[str, Kind] = field(default_factory=dict)
    objects: dict[str, Obj] = field(default_factory=dict)   # in source order
    map: dict[tuple[str, str], str] = field(default_factory=dict)  # (room, dir) -> room
    variables: dict[str, Variable] = field(default_factory=dict)
    actions: dict[str, Action] = field(default_factory=dict)
    rules: list[Rule] = field(default_factory=list)
    phrases: list[PhraseDef] = field(default_factory=list)
    either_or: dict[str, tuple[str, bool]] = field(default_factory=dict)  # adj -> (flag, value)
    value_properties: dict[str, str] = field(default_factory=dict)        # name -> kind
    notes: list[str] = field(default_factory=list)

    # ------------------------------------------------------------ queries
    def is_a(self, kind: str, ancestor: str) -> bool:
        while kind is not None:
            if kind == ancestor:
                return True
            kind = self.kinds[kind].parent if kind in self.kinds else None
        return False

    def rooms(self) -> list[Obj]:
        return [o for o in self.objects.values() if self.is_a(o.kind, "room")]

    def things(self) -> list[Obj]:
        return [o for o in self.objects.values() if not self.is_a(o.kind, "room")]

    def find(self, phrase: str) -> Obj | None:
        """An object by name, or by any unambiguous shortening of it, as in
        Inform 7 ('the Foyer' for 'Foyer of the Opera House')."""
        words = strip_article(phrase).lower().split()
        if not words:
            return None
        if phrase.lower().strip() in ("player", "the player", "yourself"):
            return self.objects.get("yourself")
        exact = [o for o in self.objects.values() if o.name.lower().split() == words]
        if exact:
            return exact[0]
        def fits(o):
            name = o.name.lower().split()
            it = iter(name)
            return all(w in it for w in words)          # words appear in order
        matches = [o for o in self.objects.values() if fits(o)]
        return matches[0] if len(matches) == 1 else None


def strip_article(phrase: str) -> str:
    p = phrase.strip()
    for a in ARTICLES:
        if p.lower().startswith(a):
            return p[len(a):].strip()
    return p


def unquote(s: str) -> str:
    s = s.strip()
    return s[1:-1] if len(s) >= 2 and s[0] == s[-1] == '"' else s


# ====================================================================== build
class ModelBuilder:
    def __init__(self, problems: Problems):
        self.m = WorldModel()
        self.p = problems
        for name, (parent, flags) in BUILTIN_KINDS.items():
            self.m.kinds[name] = Kind(name, parent, set(flags))
        for a in ACTIONS:
            self.m.actions[a.name] = Action(a.name, a.applying, a, a.out_of_world)
        self.m.objects["yourself"] = Obj("yourself", "person", Location(0), proper=True)
        self.last_object: Obj | None = None          # what 'It' means
        self.last_room: Obj | None = None            # whose paragraph we are in

    def build(self, sentences: list[Sentence]) -> WorldModel:
        for s in sentences:                          # pass 1: names
            if not s.is_rule:
                self.declare_names(s)
        self.last_object = self.last_room = None
        for i, s in enumerate(sentences):            # pass 2: meaning
            if s.is_rule:
                self.rule(s)
            else:
                self.assertion(s, first=(i == 0))
        return self.m

    # ------------------------------------------------------------ pass 1
    def declare_names(self, s: Sentence) -> None:
        t = s.text.rstrip(".").strip()
        m = re.match(r"^(.+?) is an? ((?:dark |lit )?room)$", t, re.I)
        if m:
            self.new_object(m.group(1), "room", s.where)
            return
        m = re.match(r"^an? (.+?) is a kind of (.+)$", t, re.I)
        if m:
            name, parent = m.group(1).lower(), strip_article(m.group(2)).lower()
            self.m.kinds[name] = Kind(name, parent, where=s.where)

    def new_object(self, phrase: str, kind: str, where: Location) -> Obj:
        name = strip_article(phrase)
        existing = self.m.find(name)
        if existing and existing.name.lower() == name.lower():
            return existing
        obj = Obj(name, kind, where)
        obj.proper = phrase.strip()[:1].isupper() and not phrase.lower().startswith(ARTICLES) \
            and kind != "room"
        self.m.objects[name] = obj
        return obj

    def object_for(self, phrase: str, where: Location, kind: str = "thing") -> Obj:
        """The object a phrase names, creating it (as KIND) if it is new."""
        found = self.m.find(phrase)
        if found:
            return found
        return self.new_object(phrase, kind, where)

    # ------------------------------------------------------------ pass 2
    def assertion(self, s: Sentence, first: bool) -> None:
        t = " ".join(s.text.split())
        if first and re.match(r'^"[^"]+"( by .+)?$', t):
            m = re.match(r'^"([^"]+)"(?: by (.+))?$', t)
            self.m.title = m.group(1)
            if m.group(2):
                self.m.author = unquote(m.group(2).rstrip("."))
            return
        if t.startswith('"'):                        # a bare quoted sentence
            self.bare_text(s, t)
            return
        body = t[:-1].strip() if t.endswith(".") else t
        for pattern, handler in self.PATTERNS:
            m = re.match(pattern, body, re.I)
            if m:
                handler(self, s, m)
                return
        self.p.problem(s.where, s.text, "I7-lite does not understand this sentence "
                       "(see docs/I7_LITE.md for the forms it knows).")

    def bare_text(self, s: Sentence, t: str) -> None:
        """A quoted sentence straight after a room is its description; after a
        thing, its initial appearance (Inform 7's rule)."""
        target = self.last_object
        if target is None:
            self.p.problem(s.where, t, "there is no room or thing for this text to describe.")
            return
        prop = "description" if self.m.is_a(target.kind, "room") else "initial appearance"
        self.set_text(s, target, prop, t)

    def set_text(self, s: Sentence, obj: Obj, prop: str, quoted: str) -> None:
        try:
            obj.texts[prop] = parse_text(quoted)
        except TextError as e:
            self.p.problem(s.where, quoted, f"the text is malformed: {e}.")

    # -- handlers (each gets the sentence and its regex match) --
    def story_property(self, s, m):
        prop, value = m.group(1).lower(), m.group(2).strip()
        if prop in ("headline", "genre", "description"):
            if prop == "headline":
                self.m.headline = unquote(value)
        elif prop == "release number" and value.isdigit():
            self.m.release = int(value)
        else:
            self.p.problem(s.where, s.text, f"the story {prop} should be a text or number.")

    def max_score(self, s, m):
        self.m.max_score = int(m.group(1))

    def use_option(self, s, m):
        option = m.group(1).lower()
        if option == "scoring":
            self.m.scoring = True
        elif option == "no scoring":
            self.m.scoring = False
        else:
            self.m.notes.append(f"line {s.where.line}: 'Use {option}' has no effect in I7-lite")

    def is_room(self, s, m):
        room = self.object_for(m.group(1), s.where, "room")
        room.kind = "room"
        if m.group(2) and m.group(2).strip().lower() == "dark":
            room.unflags.add("LITBIT")
        self.last_object = self.last_room = room

    def map_connection(self, s, m):
        """X is <dir> of/from Y."""
        self.connect(s, m.group(1), m.group(2).lower(), m.group(3))

    def map_connection_reversed(self, s, m):
        """<Dir> of Y is X."""
        self.connect(s, m.group(3), m.group(1).lower(), m.group(2))

    def map_in_paragraph(self, s, m):
        """<Dir> is X. (inside the paragraph of the room being described)"""
        if self.last_room is None:
            self.p.problem(s.where, s.text, "it is not clear which room this is from.")
            return
        there = self.object_for(m.group(2), s.where, "room")
        self.link(self.last_room, m.group(1).lower(), there)

    def connect(self, s, subject: str, direction: str, other: str) -> None:
        here = self.object_for(subject, s.where, "room")
        there = self.object_for(other, s.where, "room")
        for room in (here, there):
            if not self.m.is_a(room.kind, "room"):
                self.p.problem(s.where, s.text, f"'{room.name}' is not a room.")
                return
        # 'X is north of Y': going north from Y reaches X, and back again
        self.link(there, direction, here)
        self.last_object = self.last_room = here

    def link(self, frm: Obj, direction: str, to: Obj) -> None:
        self.m.map[(frm.name, direction)] = to.name
        back = (to.name, OPPOSITE[direction])
        self.m.map.setdefault(back, frm.name)        # both ways, unless set already

    def placed(self, s, m):
        """X is [descriptor] in/on Y: 'a supporter', 'scenery', 'a scenery supporter'."""
        subject, descriptor, relation, place = m.group(1), m.group(2), m.group(3), m.group(4)
        obj = self.subject(s, subject)
        if descriptor:
            self.describe(s, obj, descriptor)
        self.place(s, obj, relation.lower(), place)
        self.last_object = obj

    def describe(self, s: Sentence, obj: Obj, descriptor: str) -> None:
        """'[a] [adjectives...] [kind]': any adjectives, then optionally a kind."""
        words = strip_article(descriptor).lower().split()
        for n in range(len(words), 0, -1):          # the longest kind at the end
            kind = " ".join(words[-n:])
            if kind in self.m.kinds:
                obj.kind = kind
                words = words[:-n]
                break
        rest = " ".join(words)
        for adj in [a for a in re.split(r",\s*|\s+and\s+", rest) if a]:
            if not self.apply_adjective(obj, adj.strip()):
                self.p.problem(s.where, s.text,
                               f"'{adj.strip()}' is not a kind or property I know.")

    def placed_called(self, s, m):
        """In Y is a kind called X."""
        relation, place, kind, name = m.group(1).lower(), m.group(2), m.group(3), m.group(4)
        obj = self.object_for(name, s.where)
        self.set_kind(s, obj, kind)
        self.place(s, obj, relation, place)
        self.last_object = obj

    def possession(self, s, m):
        """The player carries/wears X."""
        obj = self.object_for(m.group(2), s.where)
        obj.parent, obj.relation = "yourself", m.group(1).lower().rstrip("s")
        if obj.relation == "wear":
            obj.relation = "worn"
            obj.flags |= {"WEARABLEBIT", "WORNBIT"}
        else:
            obj.relation = "carried"
        self.last_object = obj

    def adjectives(self, s, m):
        """X is scenery. / It is fixed in place and lit. / The Bar is dark."""
        obj = self.subject(s, m.group(1))
        for adj in re.split(r",\s*|\s+and\s+", m.group(2)):
            if not self.apply_adjective(obj, adj.strip().lower()):
                self.p.problem(s.where, s.text, f"'{adj.strip()}' is not a property I know.")
        self.last_object = obj

    def apply_adjective(self, obj: Obj, adj: str) -> bool:
        table = {**ADJECTIVES, **self.m.either_or}
        if adj not in table:
            return False
        flag, value = table[adj]
        (obj.flags if value else obj.unflags).add(flag)
        (obj.unflags if value else obj.flags).discard(flag)
        return True

    def text_property(self, s, m):
        """The description of X is "...". (also printed name, initial appearance)"""
        prop, subject, value = m.group(1).lower(), m.group(2), m.group(3)
        obj = self.subject(s, subject)
        if prop in TEXT_PROPERTIES:
            self.set_text(s, obj, prop, value)
        elif prop in self.m.value_properties:
            obj.values[prop] = value.strip()
        else:
            self.p.problem(s.where, s.text, f"'{prop}' is not a property I know.")

    def kind_of(self, s, m):
        pass                                          # done in pass 1

    def either_or(self, s, m):
        """A thing can be shiny [or dull]."""
        adjs = [a.strip().lower() for a in re.split(r"\s+or\s+", m.group(2))]
        flag = re.sub(r"[^A-Z0-9]+", "-", adjs[0].upper()).strip("-") + "BIT"
        self.m.either_or[adjs[0]] = (flag, True)
        if len(adjs) > 1:
            self.m.either_or[adjs[1]] = (flag, False)

    def value_property(self, s, m):
        """A thing has a number called weight."""
        self.m.value_properties[m.group(3).lower()] = m.group(2).lower()

    def variable(self, s, m):
        """The trample count is a number that varies."""
        name = strip_article(m.group(1)).lower()
        self.m.variables[name] = Variable(name, m.group(2).lower(), where=s.where)

    def set_variable_or_property(self, s, m):
        """The trample count is 0.   (a variable's starting value)"""
        name = strip_article(m.group(1)).lower()
        if name in self.m.variables:
            self.m.variables[name].initial = m.group(2).strip()
            return True
        return False

    def understand(self, s, m):
        words, target = m.group(1), m.group(2).strip()
        words = [unquote(w) for w in re.split(r'\s*(?:,|\band\b|\bor\b)\s*', words) if w.strip()]
        action = self.m.actions.get(strip_article(target).lower())
        if action:
            for w in words:
                action.grammar.append((w, s.where))
            return
        obj = self.m.find(target)
        if obj:
            for w in words:
                obj.words.extend(w.lower().split("/"))
            return
        self.p.problem(s.where, s.text, f"'{target}' is neither a thing nor an action I know.")

    def new_action(self, s, m):
        name = m.group(1).strip().lower()
        spec = m.group(2).lower()
        applying = 0 if "nothing" in spec else 2 if "two" in spec else 1
        self.m.actions[name] = Action(name, applying, None, "out of world" in spec)

    # (pattern, handler): the first that matches wins, so order matters
    PATTERNS = [
        (r"^the story (headline|genre|description|release number) is (.+)$", story_property),
        (r"^the release number is (\d+)$",
         lambda self, s, m: setattr(self.m, "release", int(m.group(1)))),
        (r"^the maximum score is (\d+)$", max_score),
        (r"^use (.+)$", use_option),
        (r"^(.+?) is an? (dark |lit )?room$", is_room),
        (r"^an? (.+?) is a kind of (.+)$", kind_of),
        (r"^(.+?) is an action (applying to .+|out of world.*)$", new_action),
        (r"^(.+?) (?:is|are) (north|northeast|east|southeast|south|southwest|west|northwest|"
         r"up|down|inside|outside) (?:of|from) (.+)$", map_connection),
        (r"^(north|northeast|east|southeast|south|southwest|west|northwest|up|down|inside|"
         r"outside) of (.+?) is (.+)$", map_connection_reversed),
        (r"^(north|northeast|east|southeast|south|southwest|west|northwest|up|down|inside|"
         r"outside) is (.+)$", map_in_paragraph),
        (r"^(?:the )?(description|printed name|initial appearance|[a-z ]+?) of (.+?) is "
         r'(".*"|-?\d+|.+)$', text_property),
        (r"^(.+?) (?:is|are) an? (number|text|truth state|room|thing|object) that varies$",
         variable),
        (r"^(an? .+?|.+?) can be (.+)$", either_or),
        (r"^(an? .+?) (?:has|have) an? (number|text|truth state) called (.+)$", value_property),
        (r"^understand (.+?) as (.+)$", understand),
        (r"^the player (carries|wears) (.+)$", possession),
        (r"^(in|on) (.+?) (?:is|are) an? (.+?) called (.+)$", placed_called),
        (r"^(.+?) (?:is|are) (?:([a-z ,-]+?) )?(in|on) (.+)$", placed),
        (r"^(.+?) (?:is|are) an? ([a-z-]+)$",
         lambda self, s, m: self.kind_or_value(s, m)),
        (r"^(.+?) (?:is|are) (.+)$", lambda self, s, m: self.is_something(s, m)),
    ]

    def kind_or_value(self, s, m):
        """X is a supporter.  (or: The trample count is a ...)"""
        kind = m.group(2).lower()
        if kind in self.m.kinds:
            obj = self.subject(s, m.group(1))
            self.set_kind(s, obj, kind)
            self.last_object = obj
        else:
            self.p.problem(s.where, s.text, f"'{kind}' is not a kind I know.")

    def is_something(self, s, m):
        """The last resort: 'X is <adjectives>' or 'V is <value>'."""
        if self.set_variable_or_property(s, m):
            return
        self.adjectives(s, m)

    # ------------------------------------------------------------ helpers
    def subject(self, s: Sentence, phrase: str) -> Obj:
        if phrase.strip().lower() in ("it", "they"):
            if self.last_object is None:
                self.p.problem(s.where, s.text, "it is not clear what 'it' means here.")
                return self.object_for("nothing", s.where)
            return self.last_object
        return self.object_for(phrase, s.where)

    def set_kind(self, s: Sentence, obj: Obj, kind: str) -> None:
        kind = strip_article(kind).lower()
        if kind not in self.m.kinds:
            self.p.problem(s.where, s.text, f"'{kind}' is not a kind I know.")
            return
        obj.kind = kind

    def place(self, s: Sentence, obj: Obj, relation: str, place: str) -> None:
        holder = self.object_for(place, s.where)
        if relation == "on" and not self.m.is_a(holder.kind, "supporter"):
            self.p.problem(s.where, s.text, f"'{holder.name}' is not a supporter, so "
                           "nothing can be put on it.")
        obj.parent, obj.relation = holder.name, relation

    # ------------------------------------------------------------ rules
    STAGE_WORDS = (("when play begins", "when play begins"), ("every turn", "every turn"),
                   ("instead of", "instead"), ("before", "before"), ("after", "after"),
                   ("check", "check"), ("carry out", "carry out"), ("report", "report"))

    def rule(self, s: Sentence) -> None:
        preamble = s.text.rstrip(":").strip()
        low = preamble.lower()
        if low.startswith("to "):
            self.m.phrases.append(PhraseDef(preamble, s.body, s.where))
            return
        for words, stage in self.STAGE_WORDS:
            if low.startswith(words):
                rest = preamble[len(words):].strip()
                self.m.rules.append(Rule(stage, rest, s.body, s.where, len(self.m.rules) + 1))
                return
        self.p.unsupported(s.where, s.text, "this kind of rule")


def build_model(sentences: list[Sentence], problems: Problems) -> WorldModel:
    return ModelBuilder(problems).build(sentences)
