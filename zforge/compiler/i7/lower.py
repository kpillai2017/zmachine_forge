"""Lowering: the world model -> ZIL-lite source text (docs/I7_TO_ZIL.md).

The output is ordinary ZIL-lite, compiled by zforge's ZIL compiler, and
written out by `--emit-zil` so every construct can be studied as the ZIL
it becomes. Each generated routine starts with a comment naming the
source sentence it came from."""

from __future__ import annotations

import re
from dataclasses import dataclass

from zforge.compiler.i7.model import Obj, Rule, WorldModel
from zforge.compiler.i7.phrases import PhraseLowerer
from zforge.compiler.i7.problems import Location, Problems
from zforge.compiler.i7.standard import ACTIVITIES, DIRECTIONS, INTERNAL_RULES, LIBRARY_RULES, \
    STAGES, TESTING_ACTIONS, zil_name, zil_string
from zforge.compiler.i7.text import parse_text

# ZIL names the library already uses: generated names must not clash
RESERVED = {"PLAYER", "HERE", "LIT", "PRSA", "PRSO", "PRSI", "GO", "SCORE", "TURN-COUNT",
            "ROOMS", "STORY-ENDED", "END-SAYING", "OUT-OF-WORLD", "SILENTLY", "GOING-TO",
            "GOING-FROM", "GOING-DOOR", "EXAMINE-SAID", "DESCRIBE-ROOM",
            "LIBRARY-FLAGS", "TRY", "RUN-ACTION", "FOLLOW-RULES", "BANNER", "YES?"}
# ... and every library rule's routine and response routines (TAKE-REPORT-A)
RESERVED |= {r.routine for r in LIBRARY_RULES.values()}
RESERVED |= {f"{r.routine}-{letter}" for r in LIBRARY_RULES.values() for letter, _ in r.responses}
DIRECTION_PROPS = {name: name.upper() for name, _, _ in DIRECTIONS}   # inside -> INSIDE
DICT_WORD = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class Names:
    """Unique ZIL atoms for everything the game defines."""
    def __init__(self):
        """Start with the names the library already uses, so none is reused."""
        self.used = set(RESERVED)

    def new(self, base: str) -> str:
        """A fresh ZIL name for BASE: 'brass lamp' -> BRASS-LAMP, or BRASS-LAMP-2 if taken."""
        atom = zil_name(base) or "X"
        candidate, n = atom, 2
        while candidate in self.used:
            candidate, n = f"{atom}-{n}", n + 1
        self.used.add(candidate)
        return candidate


def article_code(obj: Obj) -> int:
    """0 = none (proper-named), 1 = a, 2 = an, 3 = some (plural-named),
    4 = the author's own (ARTICLE-TEXT)."""
    if obj.proper or "PROPERBIT" in obj.flags:
        return 0
    if obj.article is not None:
        return 4
    if "PLURALBIT" in obj.flags:
        return 3
    return 2 if obj.name[:1].lower() in "aeiou" else 1


@dataclass
class Grammar:
    """A parsed action's grammar line: verb followed by tokens (noun, prepositions, ...)."""
    verb: str
    tokens: list[str]            # the ZIL words after the verb: OBJECT, prepositions


# RULES, ACTIONS and TREE do not list themselves in ACTIONS
TESTING_ACTION_NAMES = frozenset(a.name for a in TESTING_ACTIONS)


class Lowerer:
    """Converts a world model to ZIL-lite source text, writing objects, rules, and actions."""
    def __init__(self, model: WorldModel, problems: Problems, filename: str):
        """Start with empty output; the tables below fill up as the model is lowered."""
        self.m = model
        self.p = problems
        self.filename = filename
        self.names = Names()
        self.atom: dict[str, str] = {"yourself": "PLAYER"}          # object name -> atom
        self.out: list[str] = []
        self.routines: list[str] = []                                # generated routines
        # book -> stage -> [(specificity, routine, group)]; group 0 = 'first',
        # 1 = normal, 2 = 'last' (sorted before specificity)
        self.rulebooks: dict[str, dict[str, list[tuple[tuple, str, int]]]] = {}
        self.phrases = PhraseLowerer(self)
        self.extra_globals: list[str] = []                           # e.g. [one of] counters
        self.traced: set[str] = set()                                # --testing wrappers

    # ------------------------------------------------------------ entry
    def lower(self) -> str:
        """Generate the complete ZIL-lite output from the world model."""
        m = self.m
        # Assign atoms to every object, variable, and action for reference.
        for o in m.objects.values():
            if o.name != "yourself":
                self.atom[o.name] = self.names.new(o.name)
        self.var_atom = {v: self.names.new(v) for v in m.variables}
        self.action_atom = {a: zil_name(a) for a in m.actions}
        self.phrases.declare(m.phrases)
        # Emit sections: header, directions, objects, variables, rules, actions, activities.
        self.header()
        self.directions()
        self.objects()
        if m.testing:                                # TREE walks every room and thing
            self.emit("<GLOBAL ALL-OBJECTS <LTABLE "
                      + " ".join("," + a for a in self.atom.values()) + ">>", "")
        self.variables()
        self.rules()
        self.actions()
        self.activities()
        # These need every rule to exist first: the listings that name rules, and
        # the response routines the author may have changed.
        self.check_listings()
        self.responses()
        if self.extra_globals:
            self.emit('"--- state for [one of] texts"', *self.extra_globals, "")
        # Routines were collected along the way; they go after the tables and globals.
        self.out.extend(self.routines)
        return "\n".join(self.out) + "\n"

    def emit(self, *lines: str) -> None:
        """Add output lines to the generated ZIL-lite text."""
        self.out.extend(lines)

    def header(self) -> None:
        """Write the ZIL-lite header: version, constants, library includes, story metadata."""
        m = self.m
        rooms = m.rooms()
        if not rooms:
            self.p.problem(self.where0(), "(the whole source)", "there are no rooms, so the "
                           "story has nowhere to begin. Add e.g. 'The Lab is a room.'")
            return
        self.emit(f';"{self.filename}: generated by zforge from Inform 7 (I7-lite) source.',
                  ' Every routine names the sentence it came from."', "",
                  "<VERSION 5>",
                  "<DIRECTIONS " + " ".join(DIRECTION_PROPS.values()) + ">",
                  '<INSERT-FILE "lib/i7/runtime">',
                  *(['<INSERT-FILE "lib/i7/testing">'] if m.testing else []), "",
                  f"<CONSTANT STORY-TITLE {zil_string(m.title)}>",
                  f"<CONSTANT STORY-AUTHOR {zil_string(m.author)}>",
                  f"<CONSTANT STORY-HEADLINE {zil_string(m.headline)}>",
                  f"<CONSTANT RELEASE-NUMBER {m.release}>",
                  f"<CONSTANT SCORING {1 if m.scoring else 0}>",
                  f"<CONSTANT MAX-SCORE {m.max_score}>",
                  f"<CONSTANT FIRST-ROOM ,{self.atom[rooms[0].name]}>", "")

    def where0(self) -> Location:
        """Where to report a problem that belongs to no one line of the source."""
        return Location(1)

    # ------------------------------------------------------------ world
    def directions(self) -> None:
        """One object per direction: Inform 7 treats north as a thing the player names."""
        self.emit('"--- directions: Inform 7 treats north as an object (the noun of going)"')
        for name, abbrev, _ in DIRECTIONS:
            extra = [w for w in self.m.direction_words.get(name, []) if DICT_WORD.match(w)]
            words = " ".join(w.upper() for w in (name, abbrev, *extra))
            self.emit(f'<OBJECT DIR-{name.upper()} (DESC "{name}") (SYNONYM {words}) '
                      f"(DIR-PROP ,P?{DIRECTION_PROPS[name]}) (FLAGS PROPERBIT)>")
        self.emit("")

    def objects(self) -> None:
        """Write ZIL OBJECT forms for all rooms and things."""
        own_flags = sorted({flag for flag, _ in self.m.either_or.values()})
        if own_flags:
            self.emit(";\"In ZIL a flag exists once an object uses it: this object (never",
                      "  anywhere) declares the flags of this story's either/or properties.\"",
                      f"<OBJECT STORY-FLAGS (DESC \"story flags\") (FLAGS {' '.join(own_flags)})>",
                      "")
        self.emit('"--- rooms and things"')
        for o in self.m.objects.values():
            if o.name == "yourself":
                continue
            self.emit(self.object_form(o))
        self.emit("")

    def object_form(self, o: Obj) -> str:
        """Generate a ZIL OBJECT form for one room or thing."""
        atom = self.atom[o.name]
        lines = [f"<OBJECT {atom}   ;\"{o.kind} (line {o.where.line})\""]
        if o.parent:
            lines.append(f"    (IN {self.atom[o.parent]})")
        lines.append(f"    (DESC {zil_string(self.printed_name(o))})")
        # The words the player can use for it: the words of its own name (unless it
        # is privately-named) and its Understand words, less small words like 'the'.
        own = [] if o.private else o.name.lower().split()     # privately-named: none
        words = [w for w in (own + o.words)
                 if DICT_WORD.match(w) and w not in ("the", "a", "an", "of")]
        if words:
            lines.append("    (SYNONYM " + " ".join(dict.fromkeys(w.upper() for w in words)) + ")")
        # Attributes (ZIL calls them flags): from its kinds and its either/or properties.
        flags = self.flags_of(o)
        if flags:
            lines.append("    (FLAGS " + " ".join(sorted(flags)) + ")")
        lines.append(f"    (ARTICLE {article_code(o)})")
        if o.article is not None:
            lines.append(f"    (ARTICLE-TEXT {zil_string(o.article)})")
        # Its texts (description, initial appearance ...) become little routines;
        # the property holds the routine.
        for prop, text in self.texts_of(o).items():
            routine = self.text_routine(f"{atom}-{zil_name(prop)}", text,
                                        f"the {prop} of {o.name}", o.where)
            lines.append(f"    ({zil_name(prop)} ,{routine})")
        # Value properties: 'The weight of the rock is 5.'
        for prop, value in o.values.items():
            lines.append(f"    ({zil_name(prop)} {self.phrases.value(value, o.where)})")
        for prop, owner in self.m.property_owners.items():
            # 'Every room has a number called ...': each room has it, so it can be
            # changed (put_prop needs the property to be there, §15)
            if prop not in o.values and prop not in self.texts_of(o) \
                    and self.m.is_a(o.kind, owner):
                lines.append(f"    ({zil_name(prop)} 0)")
        # The map: one property per exit, e.g. (NORTH TO KITCHEN).
        for direction, to in self.exits_of(o):
            lines.append(f"    ({DIRECTION_PROPS[direction]} TO {self.atom[to]})")
        if o.sides:                                   # a door: its two rooms
            if len(o.sides) != 2:
                self.p.problem(o.where, o.name, f"a door needs two sides (one in each room), "
                               f"but '{o.name}' has {len(o.sides)}.")
            for prop, (room, _) in zip(("SIDE-A", "SIDE-B"), o.sides, strict=False):
                lines.append(f"    ({prop} {self.atom[room]})")
        if o.key:
            lines.append(f"    (WITH-KEY {self.atom[o.key]})")
        return "\n".join(lines) + ">"

    def exits_of(self, room: Obj) -> list[tuple[str, str]]:
        """(direction, room-or-door): the map, plus exits that lead to doors."""
        exits = {d: to for (r, d), to in self.m.map.items() if r == room.name}
        for door in self.m.objects.values():
            for side, direction in door.sides:
                if side == room.name:
                    exits[direction] = door.name
        return list(exits.items())

    def kind_chain(self, o: Obj) -> list:
        """The object's kinds, most specific first."""
        chain, kind = [], o.kind
        while kind:
            chain.append(self.m.kinds[kind])
            kind = self.m.kinds[kind].parent
        return chain

    def printed_name(self, o: Obj) -> str:
        """The name the player sees: its own printed name, else its kind's, else its name."""
        if o.printed is not None:
            return o.printed
        for k in self.kind_chain(o):
            if k.printed is not None:
                return k.printed
        return o.name

    def texts_of(self, o: Obj) -> dict:
        """The object's texts, with its kinds' usual ones where it has none."""
        texts = {}
        for k in reversed(self.kind_chain(o)):
            texts.update(k.texts)
        texts.update(o.texts)
        return texts

    def flags_of(self, o: Obj) -> set[str]:
        """Its attributes: its kinds' flags, most general kind first (so a more specific
        kind can take one away), then its own either/or properties."""
        flags: set[str] = set()
        for k in reversed(self.kind_chain(o)):        # kind flags, most general first
            flags = (flags | k.flags) - k.unflags
        flags = (flags | o.flags) - o.unflags
        if o.proper:
            flags.add("PROPERBIT")
        return flags

    def text_routine(self, base: str, text, what: str, where: Location | None = None) -> str:
        """Turn one text into a routine that prints it; return the routine's name.
        Texts are routines because substitutions like [if ...] must run when printed."""
        name = self.names.new(base)
        body = self.phrases.tell(text, sentence_break=False, where=where)
        self.routines.append(f'<ROUTINE {name} ()   ;"{what}"\n    {body}>')
        return name

    def names_prop(self, name: str) -> str:
        """A value property's ZIL name: 'weight' -> WEIGHT."""
        return zil_name(name)

    def variables(self) -> None:
        """Write ZIL GLOBAL declarations for all variables."""
        for prop in self.m.value_properties:
            self.emit(f"<PROPDEF {self.names_prop(prop)} 0>")
        if not self.m.variables:
            return
        self.emit('"--- variables"')
        for name, v in self.m.variables.items():
            init = self.phrases.value(v.initial, v.where) if v.initial else "0"
            self.emit(f'<GLOBAL {self.var_atom[name]} {init}>   ;"{name}: a {v.kind} that varies"')
        self.emit("")

    # ------------------------------------------------------------ rules
    def rules(self) -> None:
        """Write ZIL routines for each rule, filing them into rulebooks by action and stage."""
        self.named_rules: dict[str, str] = {}          # author's rule name -> routine
        for rule in self.m.rules:
            self.rule(rule)

    def rule(self, rule: Rule) -> None:
        """Write a ZIL routine for one rule, or dispatch to activity_rule if it's an activity."""
        stage = rule.stage
        if stage == "":                                 # This is the X rule: (unlisted)
            self.named_rules[rule.named] = self.rule_routine(rule, "", default="<RFALSE>")
            return
        # Rules that belong to no action go into their own rulebooks, in source order.
        if stage in ("when play begins", "every turn"):
            guard = ""
            if stage == "every turn" and rule.preamble.lower().startswith("when "):
                guard = self.phrases.condition(rule.preamble[5:], rule.where)
            name = self.rule_routine(rule, guard, default="<RFALSE>")
            book = "WHEN-PLAY-BEGINS" if stage == "when play begins" else "EVERY-TURN"
            self.add_rule(book, "", (0,), name, rule.placement)
            return
        if stage.startswith("activity "):
            self.activity_rule(rule, stage[len("activity "):])
            return
        # Everything else is about an action: 'Instead of taking the lamp when ...'.
        # The pattern gives the actions it covers, a guard (its conditions) and how
        # specific it is, which decides its place in the rulebook.
        pattern = self.phrases.action_pattern(rule.preamble, rule.where)
        if pattern is None:
            return
        # A body that finishes without deciding: Instead and After rules stop the
        # action (as in Inform 7); the other stages let it carry on.
        default = "<RTRUE>" if stage in ("instead", "after") else "<RFALSE>"
        name = self.rule_routine(rule, pattern.guard, default)
        if rule.named:
            self.named_rules[rule.named] = name
        for action in pattern.actions or [""]:        # "" = every action ('doing something')
            self.add_rule(action, stage, pattern.specificity, name, rule.placement)

    def activity_rule(self, rule: Rule, stage: str) -> None:
        """'Rule for printing the name of the lamp when the lamp is lit:' - STAGE is
        before, for or after. The rule applies to the item described (an object
        activity) and/or when a condition holds. A for rule that applies makes
        the decision (so the library's own way is skipped) unless it says
        'continue the activity'; a before or after rule never stops the others."""
        activity = next(a for a in ACTIVITIES if rule.preamble.lower().startswith(a.name))
        rest = rule.preamble[len(activity.name):].strip()
        when = ""
        m = re.match(r"^(.*?)\s*\bwhen (.+)$", rest, re.I)
        if m:
            rest, when = m.group(1).strip(), m.group(2)
        if re.search(r"\bwhile\b|\(called ", rest, re.I):
            self.p.unsupported(rule.where, rule.preamble,
                               "'while ...' and '(called ...)' in an activity rule")
            return
        guards = []
        if rest:
            prep = activity.preposition
            if not prep or not rest.lower().startswith(prep + " "):
                what = f"'{activity.name} {prep} <something>'" if prep else f"'{activity.name}'"
                self.p.problem(rule.where, rule.preamble,
                               f"I expected {what} here, optionally followed by 'when ...'.")
                return
            guards.append(self.phrases.object_guard(",ACT-OBJ", rest[len(prep):].strip(),
                                                    rule.where))
        if when:
            guards.append(self.phrases.condition(when, rule.where))
        guard = self.phrases.all_of(guards)
        name = self.rule_routine(rule, guard, "<RTRUE>" if stage == "for" else "<RFALSE>")
        if rule.named:
            self.named_rules[rule.named] = name
        specificity = (sum(1 for g in guards if g),)
        self.add_rule(activity.atom, stage, specificity, name, rule.placement)

    def activities(self) -> None:
        """One global per library activity (activities.zil): its before, for and
        after rulebooks, the most specific rule first (as for actions)."""
        self.emit('"--- activities"')
        for activity in ACTIVITIES:
            tables = []
            for stage in ("before", "for", "after"):
                entries = self.rulebooks.get(activity.atom, {}).get(stage, [])
                order = sorted(enumerate(entries),
                               key=lambda e: (e[1][2], tuple(-x for x in e[1][0]), e[0]))
                tables.append("<LTABLE" + "".join(" ," + r for _, (_, r, _) in order) + ">")
            self.emit(f"<GLOBAL {activity.atom} <TABLE {' '.join(tables)}>>")
        self.emit("")

    def rule_routine(self, rule: Rule, guard: str, default: str) -> str:
        """Write the routine for one rule and return its name.

        The guard (the rule's conditions) comes first: if they don't hold, the routine
        returns false at once - 'this rule does not apply'. DEFAULT is what the rule
        decides if its body finishes without deciding."""
        name = self.names.new(f"RULE-{rule.number}")
        heading = " ".join(f"{rule.stage} {rule.preamble}".split()) or f"the {rule.named}"
        body = self.phrases.body(rule.body)           # first: it may make 'let' locals
        locals_ = self.phrases.locals_list([], self.phrases.take_aux())
        lines = [f'<ROUTINE {name} ({locals_})   ;"{heading} (line {rule.where.line})"']
        if guard:
            lines.append(f"    <COND (<NOT {guard}> <RFALSE>)>")
        if self.m.testing:                            # RULES: it applies
            label = rule.named or rule.heading or heading
            lines.append(f"    <RULE-APPLIES {zil_string(label)}>")
        lines.extend("    " + line for line in body)
        lines.append(f"    {default}>")
        self.routines.append("\n".join(lines))
        return name

    def add_rule(self, book: str, stage: str, specificity: tuple, routine: str,
                 placement: str = "") -> None:
        """File a rule under BOOK and STAGE. The tables are sorted later: by GROUP
        (first / normal / last), then by how specific the rule is."""
        group = {"first": 0, "": 1, "last": 2}[placement]
        self.rulebooks.setdefault(book, {}).setdefault(stage, []).append(
            (specificity, routine, group))

    # ------------------------------------------------------------ actions
    def actions(self) -> None:
        """Write ZIL SYNTAX declarations and rulebook globals for all actions (ADR-016)."""
        self.emit('"--- rulebooks and actions"')
        for book in ("WHEN-PLAY-BEGINS", "EVERY-TURN"):
            entries = self.rulebooks.get(book, {}).get("", [])     # source order, but
            rules = [r for _, r, _ in sorted(entries, key=lambda e: e[2])]   # first/last
            self.emit(f"<GLOBAL {book}-RULES <LTABLE {' '.join(',' + r for r in rules)}>>")
        self.emit(self.rulebook_global("GENERAL-RULES", ""))
        # For each action: its rulebook tables, its V- routine (which runs them),
        # and one SYNTAX line for each way the player can type it.
        for name, action in self.m.actions.items():
            atom = self.action_atom[name]
            self.emit(self.rulebook_global(f"{atom}-RULES", name))
            prelude = "<SETG OUT-OF-WORLD 1> " if action.out_of_world else ""
            if action.standard and action.standard.variables:    # going: room gone to, ...
                prelude += f"<{action.standard.variables}> "
            if self.m.testing and name not in TESTING_ACTION_NAMES:
                self.routines.append(self.listed_action(atom, name, action.applying, prelude))
            else:
                self.routines.append(f'<ROUTINE V-{atom} ()   ;"the {name} action"\n'
                                     f"    {prelude}<RUN-ACTION ,{atom}-RULES>>")
            # Its grammar: the library's lines, then the author's Understand lines,
            # less any the author told us to forget.
            library = Location(0)                     # before every line of the source
            grammar = [(g, library) for g in (action.standard.grammar
                                              if action.standard else ())]
            grammar += action.grammar
            grammar = [(g, w) for g, w in grammar if not self.forgotten(g, name, w)]
            for line, where in grammar:
                for g in self.expand_grammar(line, action.applying, name, where):
                    words = " ".join([g.verb, *g.tokens])
                    self.emit(f"<SYNTAX {words} = V-{atom}>")
        # going: one grammar line (and a tiny routine) per direction
        self.emit("<SYNTAX GO OBJECT = V-GOING>")
        for dname, abbrev, _ in DIRECTIONS:
            up = dname.upper()
            self.emit(f"<SYNTAX {up} = V-GO-{up}>  <SYNTAX {abbrev.upper()} = V-GO-{up}>  "
                      f"<SYNTAX GO {up} = V-GO-{up}>")
            self.routines.append(f"<ROUTINE V-GO-{up} ()\n    <SETG PRSO ,DIR-{up}> "
                                 f"<SETG PRSA ,V?GOING> <V-GOING>>")
        for direction, words in self.m.direction_words.items():   # Understand "plugh" as north
            for w in words:
                if DICT_WORD.match(w):
                    self.emit(f"<SYNTAX {w.upper()} = V-GO-{direction.upper()}>")
        # 'Understand the command "grab" as "take"': a new word for an old verb.
        verbs = {line.split()[1] for line in self.out if line.startswith("<SYNTAX ")}
        for new, old in self.m.command_synonyms:          # Understand the command "grab" ...
            if old.upper() not in verbs:
                self.p.problem(self.where0(), f'Understand the command "{new}" as "{old}"',
                               f"'{old}' is not a command I know.")
            else:
                self.emit(f"<VERB-SYNONYM {old.upper()} {new.upper()}>")
        doors = [self.atom[o.name] for o in self.m.objects.values() if o.sides]
        self.emit(f"<GLOBAL DOORS <LTABLE {' '.join(',' + d for d in doors)}>>")
        self.emit("<SYNTAX UNDO = V-UNDO>", "<ROUTINE V-UNDO () <RTRUE>>", "")

    def forgotten(self, line: str, action: str, where) -> bool:
        """'Understand the command "open" as something new.' / 'Understand
        nothing as dropping.': grammar written before such a sentence (the
        library's included) no longer counts."""
        verb = line.split()[0].lower()
        for said in (self.m.forgotten_commands.get(verb), self.m.ungrammatical.get(action)):
            if said is not None and where.line < said.line:
                return True
        return False

    @staticmethod
    def listed_action(atom: str, name: str, applying: int, prelude: str) -> str:
        """A --testing build: the action routine tells ACTIONS when it starts
        and how it ends. 'putting it on' prints as 'putting' + the book +
        'on' + the table."""
        verb, _, rest = name.partition(" it ")
        parts = f"{zil_string(verb)} {zil_string(rest) if rest else 0} {applying}"
        return (f'<ROUTINE V-{atom} ("AUX" R)   ;"the {name} action"\n'
                f"    {prelude}<ACTION-STARTS {parts}>\n"
                f"    <SET R <RUN-ACTION ,{atom}-RULES>>\n"
                f"    <ACTION-ENDS {parts} .R>\n"
                f"    <RETURN .R>>")

    def rulebook_global(self, global_name: str, action: str) -> str:
        """Six LTABLEs, one per stage: the library's rules and the author's,
        most specific first (ties: library first, then source order).
        Listing sentences move named rules first: a rule 'listed instead of'
        another takes its place, 'before'/'after' goes next to it."""
        std = self.m.actions[action].standard if action else None
        tables = []
        for stage in STAGES:
            # an entry: [group, specificity, order, routine, name]; group 0 = listed first,
            # 1 = normal, 2 = listed last; order: library i, the author's 1000 + i
            entries = [[1, (0,), i, r.routine, r.name]
                       for i, r in enumerate(std.rules.get(stage, ()) if std else ())]
            entries += [[group, spec, 1000 + i, r, self.rule_name_of(r)] for i, (spec, r, group)
                        in enumerate(self.rulebooks.get(action, {}).get(stage, []))]
            if action:
                entries = self.apply_listings(entries, (stage, action))
            entries.sort(key=lambda e: (e[0], tuple(-x for x in e[1]), e[2]))
            if self.m.testing and action not in TESTING_ACTION_NAMES:   # RULES: library rules too
                for e in entries:
                    if e[2] < 1000:
                        e[3] = self.traced_library_rule(e[3], e[4])
            tables.append("<LTABLE " + " ".join("," + e[3] for e in entries) + ">")
        return f"<GLOBAL {global_name} <TABLE {' '.join(tables)}>>"

    def traced_library_rule(self, routine: str, name: str) -> str:
        """A --testing build: a wrapper that says the library rule applies,
        then runs it. (A library rule's conditions are its action's, so it
        applies whenever it is reached - Inform 7 traces it the same way.)"""
        wrapper = f"TRACED-{routine}"
        if wrapper not in self.traced:
            self.traced.add(wrapper)
            self.routines.append(f'<ROUTINE {wrapper} ()   ;"RULES: the {name}"\n'
                                 f"    <RULE-APPLIES {zil_string(name)}>\n"
                                 f"    <RETURN <{routine}>>>")
        return wrapper

    def rule_name_of(self, routine: str) -> str | None:
        """The author's name for a rule's routine, if the rule has one."""
        return next((n for n, r in self.named_rules.items() if r == routine), None)

    def apply_listings(self, entries: list, book: tuple[str, str]) -> list:
        """Apply the author's listing sentences to one rulebook's ENTRIES:
        'The X rule is not listed in ...', '... is listed first/last in ...',
        '... is listed instead of / before / after the Y rule in ...'.
        Each entry is [group, specificity, order, routine, rule name]."""
        for li in self.m.listings:
            if li.how == "not listed":
                if li.rulebook in (None, book):
                    entries = [e for e in entries if e[4] != li.rule]
                continue
            if li.rulebook != book:
                continue
            routine = self.named_rules.get(li.rule)
            if routine is None:                     # only the author's rules can be listed
                continue
            if li.how in ("in", "first", "last"):
                group = {"in": 1, "first": 0, "last": 2}[li.how]
                entries = [e for e in entries if e[3] != routine]
                entries.append([group, (0,), 999, routine, li.rule])
                continue
            target = next((e for e in entries if e[4] == li.other), None)
            if target is None:
                continue                            # reported by check_listings
            entries = [e for e in entries if e[3] != routine]
            if li.how == "instead of":
                target[3], target[4] = routine, li.rule
            else:                                   # before / after: right next to it
                step = -0.5 if li.how == "before" else 0.5
                entries.append([target[0], target[1], target[2] + step, routine, li.rule])
        return entries

    def check_listings(self) -> None:
        """Every rule named in a listing or response edit must exist."""
        known = set(LIBRARY_RULES) | set(self.named_rules)
        for li in self.m.listings:
            for name in (li.rule, li.other):
                if name and name not in known:
                    self.p.problem(li.where, f"the {name}", self.unknown_rule(name))
            if li.how != "not listed" and li.rule in LIBRARY_RULES:
                self.p.unsupported(li.where, f"the {li.rule}",
                                   "moving a library rule (it can be unlisted, or another "
                                   "rule listed instead of it)")
            if li.rulebook and li.rulebook[1] not in self.m.actions:
                self.p.problem(li.where, f"the {' '.join(li.rulebook)} rulebook",
                               f"'{li.rulebook[1]}' is not an action I know.")
        for (name, letter), (_, where) in self.m.response_edits.items():
            rule = LIBRARY_RULES.get(name)
            if rule is None:
                self.p.problem(where, f"the {name} response ({letter})", self.unknown_rule(name))
            elif letter not in dict(rule.responses):
                self.p.problem(where, f"the {name} response ({letter})",
                               f"that rule has no response ({letter}) in I7-lite (it has "
                               f"{', '.join(dict(rule.responses)) or 'none'}).")

    @staticmethod
    def unknown_rule(name: str) -> str:
        """The problem message for a listing that names a rule nobody defined."""
        return (f"there is no rule called '{name}'. (I7-lite's library rules are listed in "
                "docs/I7_LITE.md; the author's own are named with '(this is the ... rule)'.)")

    # ------------------------------------------------------------ responses
    def responses(self) -> None:
        """One routine per library response, e.g. TAKE-REPORT-A, which the
        library rule calls to print it: Inform 7's text, or the author's."""
        for rule in sorted(LIBRARY_RULES.values(), key=lambda r: r.routine):
            for letter, default in rule.responses:
                edit = self.m.response_edits.get((rule.name, letter))
                text = edit[0] if edit else parse_text(default)
                # An action's rule says its response - 'say "Dropped." (A)' -
                # and a said text ending a sentence gets a line break. An
                # internal rule is Inform 6 code that prints it: no line break
                # (the real Advent: 'Please respond yes or no. > ').
                internal = rule in INTERNAL_RULES
                body = self.phrases.tell(text, sentence_break=not internal)
                self.routines.append(f'<ROUTINE {rule.routine}-{letter} ()   '
                                     f';"the {rule.name} response ({letter})"\n    {body}>')

    def expand_grammar(self, line: str, applying: int, action: str, where) -> list[Grammar]:
        """'put [something] on/onto [something]' -> SYNTAX token lists
        (one per combination of slash alternatives)."""
        # Split the line into words and [tokens]. OPTIONS holds every way of reading
        # the line so far: a word with slashes (on/onto) doubles the options.
        parts = re.findall(r"\[[^\]]+\]|[^\s\[\]]+", line.lower())
        options: list[list[str]] = [[]]
        for part in parts:
            if part.startswith("["):
                token = part[1:-1]
                if token not in ("something", "someone", "things", "any thing", "anything",
                                 "something preferably held", "thing",
                                 "things preferably held"):
                    self.p.unsupported(where, line, f"the grammar token [{token}]")
                    return []
                # [things]: several at once - TAKE ALL, DROP A AND B (ADR-035)
                flags = {"things": ["(MANY)"],
                         "things preferably held": ["(MANY", "HELD)"]}.get(token, [])
                options = [o + ["OBJECT", *flags] for o in options]
            else:
                alts = [w for w in part.split("/") if w]
                options = [o + [w.upper()] for o in options for w in alts]
        # Each reading must start with a verb and have one OBJECT slot for each
        # thing the action applies to.
        out = []
        for o in options:
            if not o or o[0] == "OBJECT":
                self.p.problem(where, line, "a grammar line must start with a verb word.")
                return []
            if o.count("OBJECT") != applying:
                self.p.problem(where, line, f"'{action}' applies to {applying} "
                               f"thing(s), but this line has {o.count('OBJECT')}.")
                return []
            out.append(Grammar(o[0], o[1:]))
        return out


def lower_model(model: WorldModel, problems: Problems, filename: str) -> str:
    """Convert a world model to ZIL-lite source text; the public entry point."""
    return Lowerer(model, problems, filename).lower()
