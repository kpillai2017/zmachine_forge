"""The world model: what an I7-lite source asserts about its world.

Built in two passes over the sentences (so forward references work):
  1. names    - every room, thing, kind, variable and action the source
                creates, so 'The Bar is south of the Foyer' can mention
                the Bar before the sentence that describes it;
  2. meaning  - placement, map, properties, rules, grammar.

Nothing here knows about ZIL: lower.py turns this model into code."""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field

from zforge.compiler.i7.problems import Location, Problems
from zforge.compiler.i7.source import BodyLine, Sentence
from zforge.compiler.i7.standard import (
    ACTIONS, ACTIVITIES, DIRECTIONS, OPPOSITE, TESTING_ACTIONS, UNSUPPORTED_ACTIVITIES,
    StandardAction)
from zforge.compiler.i7.text import Text, TextError, parse_text

ARTICLES = ("the ", "a ", "an ", "some ")
DIRECTION_NAMES = {name for name, _, _ in DIRECTIONS}
# A word the player can type for a thing: letters, digits and hyphens (the
# Z-machine dictionary holds other characters, but I7-lite keeps to these).
DICT_WORD = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# The separators of a list of names: 'A, B, and C' or 'A and B'.
LIST_SPLIT = re.compile(r",\s*(?:and\s+)?|\s+and\s+")

# either/or properties the library understands: adjective -> (flag, value)
ADJECTIVES = {
    "lit": ("LITBIT", True), "lighted": ("LITBIT", True), "dark": ("LITBIT", False),
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
NAMING = ("privately-named", "publicly-named")          # compile-time only: no flag
# built-in kinds: name -> (parent, flags every object of the kind gets)
BUILTIN_KINDS = {
    "object": (None, ()), "room": ("object", ("ROOMBIT", "LITBIT")),
    "thing": ("object", ()), "container": ("thing", ("CONTAINERBIT", "OPENBIT")),         # open
    "supporter": ("thing", ("SUPPORTERBIT", "FIXEDBIT")),       # fixed in place (ADR-037)
    "door": ("thing", ("DOORBIT", "FIXEDBIT", "OPENABLEBIT")),      # closed, openable
    "device": ("thing", ("DEVICEBIT",)), "person": ("thing", ("PERSONBIT",)),
    "man": ("person", ()), "woman": ("person", ()), "animal": ("person", ()),
}
TEXT_PROPERTIES = {"description": "DESCRIPTION", "initial appearance": "INITIAL-APPEARANCE"}
DIRECTION_WORDS = ("north|northeast|east|southeast|south|southwest|west|northwest|"
                   "up|down|inside|outside")


@dataclass
class Kind:
    """A category of objects (room, thing, container, ...) with inherited flags and texts."""
    name: str
    parent: str | None
    flags: set[str] = field(default_factory=set)            # set on every instance
    unflags: set[str] = field(default_factory=set)          # cleared on every instance
    where: Location = Location(0)
    texts: dict[str, Text] = field(default_factory=dict)    # 'is usually' texts
    printed: str | None = None                              # usual printed name


@dataclass
class Obj:
    """A concrete object: a room, a thing, or a door, with its placement and properties."""
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
    phrases: list[list[str]] = field(default_factory=list)  # whole Understand phrases
    proper: bool = False
    private: bool = False                                   # privately-named: no name words
    printed: str | None = None                              # printed name, if not its name
    article: str | None = None                              # indefinite article ("some")
    sides: list[tuple[str, str]] = field(default_factory=list)  # a door: (room, direction)
    key: str | None = None                                  # what unlocks it
    kind_assumed: bool = False    # 'thing' only because nothing has said otherwise yet


@dataclass
class Variable:
    """A global variable: an object, number, text or truth state that varies."""
    name: str
    kind: str                                               # number / truth state / text / object
    initial: str = "0"
    where: Location = Location(0)


@dataclass
class Action:
    """An action the player can perform (take, look, examine, ...) with its grammar lines."""
    name: str
    applying: int                 # how many slots its grammar has: things, and the topic
    standard: StandardAction | None = None
    out_of_world: bool = False
    grammar: list[tuple[str, Location]] = field(default_factory=list)
    topic: bool = False           # it applies to a topic: its grammar has one [text]


@dataclass
class Rule:
    """A rule: a condition preamble followed by phrases to execute (or an activity rule)."""
    stage: str                  # "when play begins", "every turn", a STAGES name, or ""
                                # ("This is the X rule:" - in no rulebook until listed)
    preamble: str               # what follows the stage words, e.g. "going north in the Foyer"
    body: list[BodyLine]
    where: Location
    number: int = 0
    named: str | None = None    # "(this is the Crowther's heading rule)" -> that name
    placement: str = ""         # "first" / "last": 'The first after printing ... rule:'
    heading: str = ""           # the opening line as written, for RULES:
                                # "Instead of taking the lamp"


@dataclass
class Listing:
    """A sentence moving a named rule: 'The X rule is not listed in the Y
    rulebook.', '... is listed instead of the Z rule in the Y rulebook.'"""
    how: str                    # "not listed", "instead of", "before", "after",
                                # "first", "last" or "in"
    rule: str                   # "the room description heading rule" -> without 'the'
    other: str | None           # the rule it is placed relative to (instead of/before/after)
    rulebook: tuple[str, str] | None   # (stage, action); None = any rulebook
    where: Location


@dataclass
class PhraseDef:
    """A named phrase definition: a subroutine with parameters and a body."""
    preamble: str               # "To say foo", "To decide whether ..."
    body: list[BodyLine]
    where: Location


@dataclass
class Definition:
    """'Definition: a thing is goable if it is scenery or it is fixed in place.'
    An adjective worked out when asked: for things of a kind, or for one object."""
    adjective: str              # "goable"
    subject: str                # "thing" (a kind), or "the axehead" (one object)
    called: str | None          # 'a direction (called thataway)': another name for it
    condition: str | None       # the condition after 'if' - or None, and a body
    body: list[BodyLine]        # 'Definition: a thing is mentionable:' and lines of yes/no
    where: Location
    negated: bool = False       # the 'rather than' adjective: true when the other is not


@dataclass
class Table:
    """A topic table ('Table of Notes'): a topic column and text columns,
    for 'a topic listed in the Table of Notes' and '[reply entry]'."""
    name: str                     # 'table of notes'
    number: int                   # its TABLE-n-FIND routine
    columns: list[str]            # 'topic', 'reply', ...
    rows: list[tuple[list[str], Location]]
    where: Location


@dataclass
class WorldModel:
    """The game's complete model: objects, map, rules, variables, actions, and metadata."""
    title: str = "Untitled"
    author: str = "Anonymous"
    headline: str = "An Interactive Fiction"
    release: int = 1
    scoring: bool = False
    max_score: int = 0
    testing: bool = False          # a --testing build: RULES, ACTIONS, TREE
    kinds: dict[str, Kind] = field(default_factory=dict)
    objects: dict[str, Obj] = field(default_factory=dict)   # in source order
    map: dict[tuple[str, str], str] = field(default_factory=dict)  # (room, dir) -> room
    variables: dict[str, Variable] = field(default_factory=dict)
    actions: dict[str, Action] = field(default_factory=dict)
    rules: list[Rule] = field(default_factory=list)
    phrases: list[PhraseDef] = field(default_factory=list)
    either_or: dict[str, tuple[str, bool]] = field(default_factory=dict)  # adj -> (flag, value)
    tables: dict[str, Table] = field(default_factory=dict)   # 'table of notes' -> table
    definitions: dict[str, list[Definition]] = field(default_factory=dict)
    either_or_where: dict[str, tuple] = field(default_factory=dict)  # flag -> (where, sentence)
    value_properties: dict[str, str] = field(default_factory=dict)        # name -> kind
    direction_words: dict[str, list[str]] = field(default_factory=dict)  # 'north' -> ['plugh']
    verbs: dict[str, tuple[str, str]] = field(default_factory=dict)      # 'flow': (flow, flows)
    command_synonyms: list[tuple[str, str]] = field(default_factory=list)  # ('grab', 'take')
    property_owners: dict[str, str] = field(default_factory=dict)  # 'visit count' -> 'room'
    listings: list[Listing] = field(default_factory=list)
    # (rule name, response letter) -> (the author's text, where)
    response_edits: dict[tuple[str, str], tuple[Text, Location]] = field(default_factory=dict)
    nowhere: set[tuple[str, str]] = field(default_factory=set)   # (room, dir)
    forgotten_commands: dict[str, Location] = field(default_factory=dict)  # "open" -> where
    ungrammatical: dict[str, Location] = field(default_factory=dict)       # 'Understand nothing as'
    notes: list[str] = field(default_factory=list)

    # ------------------------------------------------------------ queries
    def is_a(self, kind: str, ancestor: str) -> bool:
        """Check if KIND is ANCESTOR or a descendant of it."""
        while kind is not None:
            if kind == ancestor:
                return True
            kind = self.kinds[kind].parent if kind in self.kinds else None
        return False

    def rooms(self) -> list[Obj]:
        """All room objects in the model."""
        return [o for o in self.objects.values() if self.is_a(o.kind, "room")]

    def things(self) -> list[Obj]:
        """All non-room objects in the model."""
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


IRREGULAR = {"be": "is", "have": "has", "do": "does", "go": "goes"}


def third_person_singular(verb: str) -> str:
    """flow -> flows, reach -> reaches, carry -> carries, have -> has."""
    if verb in IRREGULAR:
        return IRREGULAR[verb]
    if re.search(r"(s|x|z|ch|sh|o)$", verb):
        return verb + "es"
    if re.search(r"[^aeiou]y$", verb):
        return verb[:-1] + "ies"
    return verb + "s"


def strip_article(phrase: str) -> str:
    """Remove leading articles (the, a, an, some) from a phrase."""
    p = phrase.strip()
    for a in ARTICLES:
        if p.lower().startswith(a):
            return p[len(a):].strip()
    return p


def blank_quotes(text: str) -> str:
    """TEXT with everything inside double quotes replaced by NUL characters,
    keeping the quote marks and the length, so that positions still line up."""
    return re.sub(r'"[^"]*"', lambda q: '"' + "\0" * (len(q.group()) - 2) + '"', text)


class QuoteBlindMatch:
    """A regular-expression match made on a blank_quotes() copy, reporting
    the real text at the same positions. It offers the parts of a match
    object that the sentence handlers use."""

    def __init__(self, match: re.Match, text: str):
        self.match, self.string = match, text

    def group(self, *numbers):
        if len(numbers) > 1:
            return tuple(self.group(n) for n in numbers)
        start, end = self.match.span(numbers[0] if numbers else 0)
        return None if start < 0 else self.string[start:end]

    def start(self, n=0):
        return self.match.start(n)

    def end(self, n=0):
        return self.match.end(n)


def unquote(s: str) -> str:
    """Remove leading and trailing quotes if present."""
    s = s.strip()
    return s[1:-1] if len(s) >= 2 and s[0] == s[-1] == '"' else s


# ====================================================================== build
REVERSED = " (with nouns reversed)"   # the end of an Understand line


class ModelBuilder:
    """Builds the world model from sentences, trying pattern patterns for each."""
    def __init__(self, problems: Problems, testing: bool = False):
        self.m = WorldModel(testing=testing)
        self.p = problems
        for name, (parent, flags) in BUILTIN_KINDS.items():
            self.m.kinds[name] = Kind(name, parent, set(flags))
        for a in ACTIONS + (TESTING_ACTIONS if testing else ()):
            self.m.actions[a.name] = Action(a.name, a.applying, a, a.out_of_world,
                                            topic=a.topic)
        self.m.objects["yourself"] = Obj("yourself", "person", Location(0), proper=True)
        self.last_object: Obj | None = None          # what 'It' means
        self.last_room: Obj | None = None            # whose paragraph we are in

    def build(self, sentences: list[Sentence]) -> WorldModel:
        """Parse all sentences into the world model in two passes (forward references work)."""
        for s in sentences:                          # pass 1: names (and tables)
            if s.table:
                self.table(s)
            elif s.text.lower().startswith("definition:"):
                continue                             # an adjective: see pass 2
            elif not s.is_rule:
                self.declare_names(s)
        self.last_object = self.last_room = None
        for i, s in enumerate(sentences):            # pass 2: meaning
            if s.table:
                continue
            if s.text.lower().startswith("definition:"):
                self.definition(s)
            elif s.is_rule:
                self.rule(s)
            else:
                self.assertion(s, first=(i == 0))
        return self.m

    DEFINITION = re.compile(r"^definition: *(?:a |an |the )?(.+?)(?: \(called ([^)]+)\))? "
                            r"(?:is|are) ([a-z][a-z-]*)(?: rather than ([a-z][a-z-]*))?"
                            r"(?: if (.+))?$", re.I | re.S)

    def definition(self, s: Sentence) -> None:
        """'Definition: a thing is heavy if its weight is greater than 5.', or
        'Definition: a thing is mentionable:' with lines that say yes or no."""
        text = s.text.rstrip().rstrip(":" if s.is_rule else ".")
        m = self.DEFINITION.match(" ".join(text.split()))
        if not m or (m.group(5) is None) == (not s.is_rule):
            self.p.problem(s.where, s.text, "a definition is written 'Definition: a thing is "
                           "heavy if ...', or ends with a colon and lines that say yes or no.")
            return
        subject, called, adjective, opposite, condition = m.groups()
        adjective = adjective.lower()
        for adj in (adjective, opposite and opposite.lower()):
            if adj and (adj in ADJECTIVES or adj in self.m.either_or):
                self.p.problem(s.where, s.text, f"'{adj}' is already an adjective here "
                               "(something can be it or not), so it cannot be defined.")
                return
        body = s.body if s.is_rule else []
        self.m.definitions.setdefault(adjective, []).append(
            Definition(adjective, subject.strip(), called, condition, body, s.where))
        if opposite:
            self.m.definitions.setdefault(opposite.lower(), []).append(
                Definition(opposite.lower(), subject.strip(), called, condition, body,
                           s.where, negated=True))

    def table(self, s: Sentence) -> None:
        """A table: I7-lite has topic tables - a 'topic' column, and columns of
        texts - for looking topics up ('a topic listed in the Table of Notes')."""
        name, columns = s.text.lower(), s.table.columns
        if name in self.m.tables:
            self.p.problem(s.where, s.text, "there is already a table with this name.")
            return
        if columns.count("topic") != 1:
            self.p.unsupported(s.where, s.text, "a table without one 'topic' column "
                               "(I7-lite has tables of topics only)")
            return
        rows = []
        for entries, where in s.table.rows:
            if len(entries) > len(columns):
                self.p.problem(where, "\t".join(entries), f"this row has {len(entries)} "
                               f"entries, but the table has {len(columns)} columns.")
                continue
            entries = entries + ["--"] * (len(columns) - len(entries))
            for column, entry in zip(columns, entries, strict=True):
                if column != "topic" and entry != "--" and not (
                        len(entry) > 1 and entry.startswith('"') and entry.endswith('"')):
                    self.p.unsupported(where, entry, "a table entry that is not a text "
                                       "in quotation marks")
            rows.append((entries, where))
        self.m.tables[name] = Table(name, len(self.m.tables) + 1, columns, rows, s.where)

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
            return
        m = re.match(r"^(?:an?|every) .+? (?:has|have) an? (number|text|truth state) called (.+)$",
                     t, re.I)
        if m:                                        # properties, so later is fine too
            self.m.value_properties[strip_article(m.group(2)).lower()] = m.group(1).lower()

    def new_object(self, phrase: str, kind: str, where: Location) -> Obj:
        """Create or retrieve an object of the given kind."""
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
        """The object a phrase names, creating it (as KIND) if it is new.
        Inform 7 infers a kind from all the sentences: something that is a
        thing only by assumption ('A and B are lighted.') becomes a room when a
        later sentence needs a room ('B is north of A.')."""
        found = self.m.find(phrase)
        if found:
            if (kind == "room" and found.kind_assumed and found.kind == "thing"
                    and found.parent is None):
                found.kind, found.kind_assumed, found.proper = "room", False, False
            return found
        obj = self.new_object(phrase, kind, where)
        obj.kind_assumed = kind == "thing"
        return obj

    # ------------------------------------------------------------ pass 2
    def assertion(self, s: Sentence, first: bool) -> None:
        """Parse an assertion sentence, trying patterns until one matches."""
        t = " ".join(s.text.split())
        # Titling sentence: "Title" or "Title" by Author (first sentence only).
        if first and re.match(r'^"[^"]+"( by .+)?$', t):
            m = re.match(r'^"([^"]+)"(?: by (.+))?$', t)
            self.m.title = m.group(1)
            if m.group(2):
                self.m.author = unquote(m.group(2).rstrip("."))
            return
        if t.startswith('"'):                        # a bare quoted sentence
            # '"...[end if]".' is the same text with the sentence's own full
            # stop after it: a text ending in ']' can't end a sentence by
            # itself, so authors add one. It is not part of the text.
            if re.match(r'^"[^"]*"\.$', t):
                t = t[:-1]
            self.bare_text(s, t)
            return
        # Try patterns in order (comma_placement must come first; order matters).
        body = t[:-1].strip() if t.endswith(".") else t
        # The patterns look for keywords ('unlocks', 'is north of', 'in'), and
        # a keyword inside a quoted text is just part of the text: 'The
        # description of the key is "...intended to unlock more than one
        # thing".' is not a sentence about unlocking. So each pattern is
        # matched against a copy with the quoted texts blanked out, and the
        # handler is given the real words at the same positions.
        blind = blank_quotes(body)
        for pattern, handler in self.PATTERNS:
            found = re.match(pattern, blind, re.I)
            m = QuoteBlindMatch(found, body) if found else None
            if m and handler(self, s, m) is not False:    # False: 'not mine after all'
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
        direction = m.group(1).lower()
        if m.group(2).lower() == "nowhere":          # 'Outside is nowhere.': no exit
            self.m.map.pop((self.last_room.name, direction), None)
            self.m.nowhere.add((self.last_room.name, direction))
            return
        there = self.object_for(m.group(2), s.where, "room")
        self.link(self.last_room, direction, there)

    def connect(self, s, subject: str, direction: str, other: str) -> None:
        # 'It is north of A and south of B', or 'The Pit is south of A,
        # southwest of B and southeast of C': several connections in one
        # sentence, split one at a time
        more = re.match(rf"^(.+?)(?:,? and|,) ({DIRECTION_WORDS}|above|below) "
                        rf"(?:(?:of|from) )?(.+)$", other, re.I)
        if more:
            self.connect(s, subject, direction, more.group(1))
            direction2 = {"above": "up", "below": "down"}.get(more.group(2).lower(),
                                                              more.group(2).lower())
            self.connect(s, subject, direction2, more.group(3))
            return
        door = self.subject(s, subject) if self.is_door_phrase(subject) else None
        if door is not None:
            # 'The grate is below the Depression': going down from the
            # Depression leads to the grate, and through it
            room = self.object_for(other, s.where, "room")
            door.sides.append((room.name, direction))
            if door.parent is None:
                door.parent, door.relation = room.name, "in"
            self.last_object = door
            return
        if self.is_door_phrase(other):
            # going west through the steps leads to the Hall, so from the
            # Hall the steps are to the east
            door, room = self.subject(s, other), self.object_for(subject, s.where, "room")
            door.sides.append((room.name, OPPOSITE[direction]))
            return
        if subject.strip().lower() in ("it", "they"):
            # 'The Library is north of the Hall. It is west of the Garden.':
            # 'It' is the room the previous sentence was about
            if self.last_object is None or not self.m.is_a(self.last_object.kind, "room"):
                self.p.problem(s.where, s.text, f"it is not clear which room "
                               f"'{subject.strip()}' means here; name the room instead.")
                return
            here = self.last_object
        else:
            here = self.object_for(subject, s.where, "room")
        there = self.object_for(other, s.where, "room")
        for room in (here, there):
            if not self.m.is_a(room.kind, "room"):
                self.p.problem(s.where, s.text, f"'{room.name}' is not a room.")
                return
        # 'X is north of Y': going north from Y reaches X, and back again
        self.link(there, direction, here)
        self.last_object = self.last_room = here

    def is_door_phrase(self, phrase: str) -> bool:
        if phrase.strip().lower() in ("it", "they"):
            return self.last_object is not None and self.m.is_a(self.last_object.kind, "door")
        obj = self.m.find(phrase)
        return obj is not None and self.m.is_a(obj.kind, "door")

    def above_below(self, s, m):
        """X is above/below Y  (= up/down from Y)."""
        self.connect(s, m.group(1), "up" if m.group(2).lower() == "above" else "down", m.group(3))

    def unlocks(self, s, m):
        """The keys unlock the grate."""
        key = self.subject(s, m.group(1))
        target = self.subject(s, m.group(2))
        target.key = key.name
        target.flags.add("LOCKABLEBIT")

    def usually(self, s, m):
        """A room is usually dark.   (a default for every object of a kind)"""
        kind = strip_article(m.group(1)).lower()
        if kind not in self.m.kinds:
            obj = self.subject(s, m.group(1))          # 'X is usually Y' of one thing
            for adj in re.split(r",\s*|\s+and\s+", m.group(2)):
                if not self.apply_adjective(obj, adj.strip().lower()):
                    self.p.problem(s.where, s.text, f"'{adj.strip()}' is not a property I know.")
            return
        k = self.m.kinds[kind]
        for adj in re.split(r",\s*|\s+and\s+", m.group(2)):
            adj = adj.strip().lower()
            table = {**ADJECTIVES, **self.m.either_or}
            if adj not in table:
                self.p.problem(s.where, s.text, f"'{adj}' is not a property I know.")
                continue
            flag, value = table[adj]
            (k.flags if value else k.unflags).add(flag)
            (k.unflags if value else k.flags).discard(flag)

    def usually_text(self, s, m):
        """The printed name of a forest is usually "Forest"."""
        prop, kind, value = m.group(1).lower(), strip_article(m.group(2)).lower(), m.group(3)
        if kind in self.m.kinds and prop == "printed name":
            self.m.kinds[kind].printed = unquote(value)
            return
        if kind not in self.m.kinds or (prop not in TEXT_PROPERTIES
                                         and self.m.value_properties.get(prop) != "text"):
            self.p.problem(s.where, s.text, "I7-lite can only give a kind a usual printed "
                           f"name, {' or '.join(TEXT_PROPERTIES)}.")
            return
        try:
            self.m.kinds[kind].texts[prop] = parse_text(value)
        except TextError as e:
            self.p.problem(s.where, value, f"the text is malformed: {e}.")

    def new_verb(self, s, m):
        """To flow is a verb.   (then [flow] prints 'flow' or 'flows')"""
        verb = m.group(1).lower()
        self.m.verbs[verb] = (verb, third_person_singular(verb))

    def command_synonym(self, s, m):
        """Understand the command "grab" as "take"."""
        new = [unquote(w).lower() for w in re.split(r"\s*(?:,|\band\b|\bor\b)\s*", m.group(1))
               if w.strip()]
        old = unquote(m.group(2)).lower()
        for word in new:
            self.m.command_synonyms.append((word, old))

    def link(self, frm: Obj, direction: str, to: Obj) -> None:
        """Create a two-way map connection, unless the reverse is set explicitly."""
        self.m.map[(frm.name, direction)] = to.name
        back = (to.name, OPPOSITE[direction])
        if back not in self.m.nowhere:               # 'Outside is nowhere.' wins
            self.m.map.setdefault(back, frm.name)    # both ways, unless set already

    def placed(self, s, m):
        """X is [descriptor] in/on Y: 'a supporter', 'scenery', 'a scenery supporter'."""
        subject, descriptor, relation, place = m.group(1), m.group(2), m.group(3), m.group(4)
        tail = m.string[m.end(1):].split(None, 1)[1]            # after 'is' / 'are'
        if self.only_adjectives(tail):          # 'The desk is fixed in place.' - not a place
            return False
        verb = m.string[m.end(1):].split(None, 1)[0].lower()      # 'is' or 'are'
        for obj in self.subjects(s, subject, verb):
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
        for chunk in [a.strip() for a in re.split(r",\s*|\s+and\s+", rest) if a.strip()]:
            # 'fixed in place' is one adjective; 'open unopenable' is two
            if self.apply_adjective(obj, chunk):
                continue
            for adj in chunk.split():
                if not self.apply_adjective(obj, adj):
                    self.p.problem(s.where, s.text, f"'{adj}' is not a kind or property I know.")

    def placed_called(self, s, m):
        """In Y is a [adjectives] kind called X."""
        relation, place, descriptor, name = m.group(1).lower(), m.group(2), m.group(3), m.group(4)
        obj = self.object_for(name, s.where)
        self.describe(s, obj, descriptor)
        self.place(s, obj, relation, place)
        self.last_object = obj

    def possession(self, s, m):
        """The player carries/wears X (or a list: 'a lamp and some coins')."""
        for obj in self.listed_objects(s, m.group(2), plural_some=False):
            obj.parent, obj.relation = "yourself", m.group(1).lower().rstrip("s")
            if obj.relation == "wear":
                obj.relation = "worn"
                obj.flags |= {"WEARABLEBIT", "WORNBIT"}
            else:
                obj.relation = "carried"
            self.last_object = obj

    def adjectives(self, s, m):
        """X is scenery. / It is fixed in place and lit. / The Bar is dark.
        Also 'A, B, and C are lighted.': with 'are', as in Inform 7, a subject
        with commas or 'and' is a list (a part not yet defined is made now)."""
        verb = m.string[m.end(1):m.start(2)].strip().lower()
        objs = self.subjects(s, m.group(1), verb)
        for adj in re.split(r",\s*|\s+and\s+", m.group(2)):
            for obj in objs:
                if not self.apply_adjective(obj, adj.strip().lower()):
                    self.p.problem(s.where, s.text, f"'{adj.strip()}' is not a property I know.")
                    break
        self.last_object = objs[-1]

    def only_adjectives(self, text: str) -> bool:
        """'fixed in place', 'scenery and fixed in place': adjectives only?"""
        table = {**ADJECTIVES, **self.m.either_or}
        chunks = [c.strip().lower() for c in re.split(r",\s*|\s+and\s+", text) if c.strip()]
        return bool(chunks) and all(c in table or c in NAMING for c in chunks)

    def apply_adjective(self, obj: Obj, adj: str) -> bool:
        if adj in NAMING:
            obj.private = adj == "privately-named"
            return True
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
        if not self.is_property(prop):
            return False                    # 'The set of keys is in ...' is not a property
        self.set_property(s, self.subject(s, subject), prop, value)

    def own_property(self, s, m):
        """The short description is "...".  (of the room or thing just named)"""
        prop = m.group(1).lower()
        if not self.is_property(prop):
            return False
        if self.last_object is None:
            self.p.problem(s.where, s.text, f"there is no room or thing to give a {prop} to.")
            return None
        self.set_property(s, self.last_object, prop, m.group(2))

    def is_property(self, prop: str) -> bool:
        return prop in (*TEXT_PROPERTIES, "printed name", "indefinite article") \
            or prop in self.m.value_properties

    def set_property(self, s, obj: Obj, prop: str, value: str) -> None:
        if prop in ("printed name", "indefinite article"):
            if not re.fullmatch(r'"[^"\[\]]*"', value.strip()):
                self.p.problem(s.where, s.text, f"the {prop} must be plain text in I7-lite "
                               "(no [substitutions]).")
            elif prop == "printed name":
                obj.printed = unquote(value)
            else:
                obj.article = unquote(value)
        elif prop in TEXT_PROPERTIES or self.m.value_properties.get(prop) == "text":
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
        self.m.either_or_where.setdefault(flag, (s.where, s.text))
        if len(adjs) > 1:
            self.m.either_or[adjs[1]] = (flag, False)

    def value_property(self, s, m):
        """A thing has a number called weight.  /  Every room has a text called ..."""
        prop = strip_article(m.group(3)).lower()
        self.m.value_properties[prop] = m.group(2).lower()
        owner = re.sub(r"^(?:an?|every)\s+", "", m.group(1).strip(), flags=re.I).lower()
        if owner in self.m.kinds:
            self.m.property_owners[prop] = owner

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

    def understand_words(self, s: Sentence, obj: Obj, text: str) -> None:
        """One Understand text for a thing: a word ("peg", "dark/black") or a
        phrase ("puzzle piece"), which only means the thing as a whole, as in
        Inform. A slash is between words: "wooden shape/bit" is "wooden shape"
        or "wooden bit"."""
        parts = text.split()
        if len(parts) == 1:
            obj.words.extend(parts[0].split("/"))
            return
        for phrase in itertools.product(*(part.split("/") for part in parts)):
            bad = [w for w in phrase if not DICT_WORD.match(w)]
            if bad:
                self.p.problem(s.where, s.text, f"'{bad[0]}' can't be a word the player types "
                               f"for {obj.name}: in I7-lite a word is made of letters, digits "
                               "and hyphens.")
                return
            obj.phrases.append(list(phrase))

    def understand(self, s, m):
        """Add grammar lines to an action, direction synonyms, or object aliases."""
        words, target = m.group(1), m.group(2).strip()
        words = [unquote(w) for w in re.split(r'\s*(?:,|\band\b|\bor\b)\s*', words) if w.strip()]
        # Understand "plugh" as north: a direction synonym (or forward slash alternatives).
        if strip_article(target).lower() in DIRECTION_NAMES:
            direction = strip_article(target).lower()
            for w in words:
                self.m.direction_words.setdefault(direction, []).extend(w.lower().split("/"))
            return
        # Understand "hang [something] on [something]" as putting it on.
        # '(with nouns reversed)': the first thing typed is the second noun;
        # the line keeps the words, for the lowerer to mark its grammar row.
        reversed_ = target.lower().endswith(REVERSED)
        if reversed_:
            target = target[:-len(REVERSED)].strip()
        action = self.m.actions.get(strip_article(target).lower())
        if action:
            for w in words:
                action.grammar.append((w + (REVERSED if reversed_ else ""), s.where))
            return
        # Understand "peg" as the brass hook: object synonyms or extra names.
        obj = self.m.find(target)
        if obj:
            for w in words:
                self.understand_words(s, obj, w.lower())
            return
        self.p.problem(s.where, s.text, f"'{target}' is neither a thing nor an action I know.")

    def new_action(self, s, m):
        name = m.group(1).strip().lower()
        spec = m.group(2).lower()
        # 'applying to one topic' / 'to one thing and one topic': the topic is
        # typed as [text] and has a grammar slot of its own
        topic = "topic" in spec
        applying = (0 if "nothing" in spec else
                    2 if "two" in spec or (topic and " and " in spec) else 1)
        self.m.actions[name] = Action(name, applying, None, "out of world" in spec, topic=topic)

    # -- rules by name: listing sentences and response edits
    @staticmethod
    def rule_name(text: str) -> str:
        return strip_article(" ".join(text.split())).lower()

    def rulebook(self, s, text: str) -> tuple[str, str] | None:
        """'the carry out looking rulebook' -> ('carry out', 'looking')."""
        t = strip_article(text).lower().removesuffix(" rulebook").strip()
        for words, stage in self.STAGE_WORDS[2:]:      # the six action stages
            if t.startswith(words + " "):
                return stage, t[len(words) + 1:].strip()
        self.p.problem(s.where, s.text, f"'{text}' is not a rulebook I7-lite knows: it has "
                       "the six rulebooks of each action, e.g. 'the check taking rulebook'.")
        return None

    def not_listed(self, s, m):
        anywhere = m.group(2).lower() == "any rulebook"
        book = None if anywhere else self.rulebook(s, m.group(2))
        if not anywhere and book is None:
            return
        self.m.listings.append(Listing("not listed", self.rule_name(m.group(1)), None, book,
                                       s.where))

    def listed_relative(self, s, m):
        book = self.rulebook(s, m.group(4))
        if book:
            self.m.listings.append(Listing(m.group(2).lower(), self.rule_name(m.group(1)),
                                           self.rule_name(m.group(3)), book, s.where))

    def listed_at(self, s, m):
        book = self.rulebook(s, m.group(3))
        if book:
            how = (m.group(2) or "in").strip().lower()
            self.m.listings.append(Listing(how, self.rule_name(m.group(1)), None, book, s.where))

    def response_edit(self, s, m):
        """The standard report taking rule response (A) is "OK."."""
        try:
            text = parse_text(m.group(3))
        except TextError as e:
            self.p.problem(s.where, m.group(3), f"the text is malformed: {e}.")
            return
        self.m.response_edits[(self.rule_name(m.group(1)), m.group(2).upper())] = (text, s.where)

    def forget_commands(self, s, m):
        """Understand the commands "open", "close" as something new."""
        for w in re.split(r"\s*(?:,|\band\b|\bor\b)\s*", m.group(1)):
            if w.strip():
                self.m.forgotten_commands[unquote(w).lower()] = s.where

    def forget_action_grammar(self, s, m):
        """Understand nothing as dropping."""
        self.m.ungrammatical[strip_article(m.group(1)).lower()] = s.where

    # (pattern, handler): the first that matches wins, so order matters
    def comma_placement(self, s, m):
        """X is <kind phrase>, below Y: the kind, then the place, as two sentences."""
        subject, what, where_ = m.group(1), m.group(2), m.group(3)
        verb = m.string[m.end(1):m.start(2)].strip()           # 'is' or 'are', as written
        self.assertion(Sentence(f"{subject} {verb} {what}", s.where), False)
        self.assertion(Sentence(f"{subject} {verb} {where_}", s.where), False)

    PATTERNS = [
        (rf"^(.+?) (?:is|are) ((?:an?|some) [^,]+), ((?:above|below|in|on|inside from|outside from"
         rf"|(?:{DIRECTION_WORDS}) (?:of|from)) .+)$", comma_placement),
        (r"^(.+? rule) response \(([a-z])\) is (\".*\")$", response_edit),
        (r"^(.+? rule) is not listed in (any rulebook|.+? rulebook)$", not_listed),
        (r"^(.+? rule) is listed (instead of|before|after) (.+? rule) in (.+? rulebook)$",
         listed_relative),
        (r"^(.+? rule) is listed (first |last )?in (.+? rulebook)$", listed_at),
        (r"^understand the commands? (.+?) as something new$", forget_commands),
        (r"^understand nothing as (.+)$", forget_action_grammar),
        (r"^the story (headline|genre|description|release number) is (.+)$", story_property),
        (r"^the release number is (\d+)$",
         lambda self, s, m: setattr(self.m, "release", int(m.group(1)))),
        (r"^the maximum score is (\d+)$", max_score),
        (r"^use (.+)$", use_option),
        (r"^(.+?) is an? (dark |lit )?room$", is_room),
        (r"^an? (.+?) is a kind of (.+)$", kind_of),
        (r"^(.+?) is an action (applying to .+|out of world.*)$", new_action),
        (r"^the (.+?) of (an? .+?) (?:is|are) usually (\".*\")$", usually_text),
        (r"^(.+?) (?:is|are) usually (.+)$", usually),
        (r"^understand the commands? (.+?) as (\".*?\")$", command_synonym),
        (r"^to ([a-z]+)(?: \(.*\))? is a verb$", new_verb),
        (r"^(.+?) (?:is|are) (above|below) (.+)$", above_below),
        (r"^(.+?) (?:unlock|unlocks) (.+)$", unlocks),
        (r"^(.+?) (?:is|are) (north|northeast|east|southeast|south|southwest|west|northwest|"
         r"up|down|inside|outside) (?:of|from) (.+)$", map_connection),
        (r"^(north|northeast|east|southeast|south|southwest|west|northwest|up|down|inside|"
         r"outside) of (.+?) is (.+)$", map_connection_reversed),
        (r"^(north|northeast|east|southeast|south|southwest|west|northwest|up|down|inside|"
         r"outside) is (.+)$", map_in_paragraph),
        (r"^(?:the )?(description|printed name|initial appearance|[a-z ]+?) of (.+?) is "
         r'(".*"|-?\d+|.+)$', text_property),
        (r'^the ([a-z ]+?) is (".*")$', own_property),
        (r"^(.+?) (?:is|are) an? (number|text|truth state|room|thing|object) that varies$",
         variable),
        (r"^(an? .+?|.+?) can be (.+)$", either_or),
        (r"^((?:an?|every) .+?) (?:has|have) an? (number|text|truth state) called (.+)$",
         value_property),
        (r"^understand (.+?) as (.+)$", understand),
        (r"^the player (carries|wears) (.+)$", possession),
        (r"^(in|on) (.+?) (?:is|are) an? (.+?) called (.+)$", placed_called),
        # greedy descriptor: 'a fixed in place thing in the Hall' splits at the last 'in'
        (r"^(.+?) (?:is|are) (?:([a-z ,-]+) )?(in|on) (.+)$", placed),
        (r"^(.+?) (?:is|are) an? ([a-z-]+)$",
         lambda self, s, m: self.kind_or_value(s, m)),
        (r"^(.+?) (?:is|are) ((?:an?|some) .+)$", lambda self, s, m: self.described(s, m)),
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

    def described(self, s, m):
        """X is an open unopenable door: adjectives, then a kind at the end."""
        words = strip_article(m.group(2)).lower().split()
        if not any(" ".join(words[-n:]) in self.m.kinds for n in range(1, len(words) + 1)):
            return False                                # not a kind: let others try
        obj = self.subject(s, m.group(1))
        self.describe(s, obj, m.group(2))
        self.last_object = obj

    def is_something(self, s, m):
        """The last resort: 'X is <adjectives>' or 'V is <value>'."""
        if self.set_variable_or_property(s, m):
            return
        self.adjectives(s, m)

    # ------------------------------------------------------------ helpers
    def subjects(self, s: Sentence, phrase: str, verb: str) -> list[Obj]:
        """The things a sentence's subject names. As in Inform 7, with 'are' a
        subject with commas or 'and' is a list: 'A red ball and a blue ball are
        in the Hall.' is two balls (a name with 'and' in it needs 'called')."""
        if verb == "are" and len([p for p in LIST_SPLIT.split(phrase) if p.strip()]) > 1:
            return self.listed_objects(s, phrase)
        return [self.subject(s, phrase)]

    def listed_objects(self, s: Sentence, phrase: str, plural_some: bool = True) -> list[Obj]:
        """One thing for each name in a list ('a top and some beads'). A new
        thing named with 'some' has 'some' as its article; in an 'are'
        sentence (plural_some) it is plural-named too, as 'Some beads are ...'
        makes it."""
        things = []
        for part in [p.strip() for p in LIST_SPLIT.split(phrase) if p.strip()]:
            new = self.m.find(part) is None
            obj = self.object_for(part, s.where)
            if new and part.lower().startswith("some "):
                if plural_some:
                    obj.flags.add("PLURALBIT")
                if obj.article is None:
                    obj.article = "some"
            things.append(obj)
        return things

    def subject(self, s: Sentence, phrase: str) -> Obj:
        if phrase.strip().lower() in ("it", "they"):
            if self.last_object is None:
                self.p.problem(s.where, s.text, "it is not clear what 'it' means here.")
                return self.object_for("nothing", s.where)
            return self.last_object
        new = self.m.find(phrase) is None
        obj = self.object_for(phrase, s.where)
        if new:
            # Inform 7: 'Some keys are in the Building.' makes plural-named
            # keys whose indefinite article is 'some'.
            rest = " ".join(s.text.split())[len(" ".join(phrase.split())):].lstrip().lower()
            if rest.startswith("are "):
                obj.flags.add("PLURALBIT")
            if phrase.strip().lower().startswith("some ") and obj.article is None:
                obj.article = "some"
        return obj

    def set_kind(self, s: Sentence, obj: Obj, kind: str) -> None:
        kind = strip_article(kind).lower()
        if kind not in self.m.kinds:
            self.p.problem(s.where, s.text, f"'{kind}' is not a kind I know.")
            return
        obj.kind = kind
        obj.kind_assumed = False

    def place(self, s: Sentence, obj: Obj, relation: str, place: str) -> None:
        holder = self.object_for(place, s.where)
        if obj is holder:
            self.p.problem(s.where, s.text, f"this puts '{obj.name}' inside itself. (A short "
                           f"name like this can mean an existing '{obj.name}': give the new "
                           "thing a different name.)")
            return
        if self.m.is_a(obj.kind, "room"):
            self.p.problem(s.where, s.text, f"'{obj.name}' is a room, and a room cannot be "
                           f"{relation} something. (A short name can mean an existing room: "
                           "give the new thing a different name.)")
            return
        if relation == "on" and not self.m.is_a(holder.kind, "supporter"):
            self.p.problem(s.where, s.text, f"'{holder.name}' is not a supporter, so "
                           "nothing can be put on it.")
        if obj.parent is not None and (obj.parent, obj.relation) != (holder.name, relation):
            # A thing can be in only one place. Inform 7 reports this as a
            # contradiction; quietly moving the thing would hide a mistake.
            # The usual cause is a short name: 'The inkpot is in the Black
            # Gallery' means the existing 'history of the inkpot' if that is
            # the only thing whose name contains 'inkpot'.
            why = (f"'{obj.name}' is already {obj.relation} '{obj.parent}' (an earlier "
                   "sentence put it there), and a thing can be in only one place.")
            if obj.name.lower() not in " ".join(s.text.split()).lower():
                why += (f" (A short name like this can mean the existing '{obj.name}': if "
                        f"you meant a new thing, give it a name that is not part of "
                        f"'{obj.name}'.)")
            self.p.problem(s.where, s.text, why)
            return
        obj.parent, obj.relation = holder.name, relation

    # ------------------------------------------------------------ rules
    STAGE_WORDS = (("when play begins", "when play begins"), ("every turn", "every turn"),
                   ("instead of", "instead"), ("before", "before"), ("after", "after"),
                   ("check", "check"), ("carry out", "carry out"), ("report", "report"))

    def rule(self, s: Sentence) -> None:
        """Parse a rule preamble and body into the model."""
        preamble = " ".join(s.text.rstrip(":").split())
        written = preamble                               # kept for RULES to show
        low = preamble.lower()
        if low.startswith("to "):
            self.m.phrases.append(PhraseDef(preamble, s.body, s.where))
            return
        number = len(self.m.rules) + 1
        m = re.match(r"^this is the (.+? rule)$", preamble, re.I)       # This is the X rule:
        if m:
            self.m.rules.append(Rule("", "", s.body, s.where, number, self.rule_name(m.group(1))))
            return
        named = None                                     # Carry out looking (this is the X rule):
        m = re.match(r"^(.*?)\s*\(this is the (.+? rule)\)$", preamble, re.I)
        if m:
            preamble, named = m.group(1), self.rule_name(m.group(2))
            low = preamble.lower()
        # 'The first after printing a parser error rule:' / 'First every turn:' /
        # 'Last carry out taking:' - first or last in its rulebook, whatever the
        # specificity. Only when a real rule follows ('Last Chance' is a room).
        placement = ""
        m = re.match(r"^(?:the |a )?(first|last) (.+?)(?: rule)?$", preamble, re.I)
        if m and re.match(r"^(rule for|before|after|instead|check|carry out|report|"
                          r"every turn|when play begins)\b", m.group(2), re.I):
            placement, preamble = m.group(1).lower(), m.group(2)
            low = preamble.lower()
        # Activities: "Rule for printing the name of the lamp", "Before
        # printing the banner text". Checked before actions, so "Before
        # printing ..." is not read as a before-rule for an action.
        m = re.match(r"^(rule for|before|after) (.+)$", preamble, re.I)
        if m:
            stage, rest = m.group(1).lower(), m.group(2)
            activity = self.activity_named(rest)
            if activity is not None:
                self.m.rules.append(Rule("activity " + ("for" if stage == "rule for" else stage),
                                         rest, s.body, s.where, number, named, placement,
                                         heading=written))
                return
            if stage == "rule for":
                known = [a for a in UNSUPPORTED_ACTIVITIES if rest.lower().startswith(a)]
                if known:
                    self.p.unsupported(s.where, s.text, f"the '{known[0]}' activity")
                else:
                    names = ", ".join(f"'{a.name}'" for a in ACTIVITIES)
                    self.p.problem(s.where, s.text, "I know no activity by that name. "
                                   f"The activities I7-lite carries out are {names}.")
                return
            for name in UNSUPPORTED_ACTIVITIES:
                if rest.lower().startswith(name):
                    self.p.unsupported(s.where, s.text, f"the '{name}' activity")
                    return
        for words, stage in self.STAGE_WORDS:
            if low.startswith(words):
                rest = preamble[len(words):].strip()
                self.m.rules.append(Rule(stage, rest, s.body, s.where, number, named,
                                         placement, heading=written))
                return
        self.p.unsupported(s.where, s.text, "this kind of rule")

    @staticmethod
    def activity_named(preamble: str):
        """The library activity a rule preamble starts with, or None."""
        low = preamble.lower()
        for activity in ACTIVITIES:               # longest names first
            if low == activity.name or low.startswith(activity.name + " "):
                return activity
        return None


def build_model(sentences: list[Sentence], problems: Problems,
                testing: bool = False) -> WorldModel:
    return ModelBuilder(problems, testing).build(sentences)
