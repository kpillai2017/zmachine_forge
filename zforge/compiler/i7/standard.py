"""The standard actions and directions: I7-lite's small 'Standard Rules'.

Each standard action lists its Inform 7 name, how many things it applies
to, its grammar (written as Inform 7 Understand lines, compiled exactly
like an author's), and the library rule routines (zforge/lib/i7/
standard.zil) that go into each stage of its rulebook - by their
Inform 7 names, in Inform 7's order, each with its responses (the text it
prints, which an author may change)."""

from __future__ import annotations

import re

from dataclasses import dataclass, field

# The six stages an action goes through, in order (Inform 7's rulebooks).
# Before, Instead and Check can stop it; Carry out does it; After and
# Report tell the player.
STAGES = ("before", "instead", "check", "carry out", "after", "report")


@dataclass(frozen=True)
class LibraryRule:
    """One of Inform 7's named library rules. An author can refer to it by
    name ('The can't take what's already taken rule is not listed in ...')
    and change what it says ('... rule response (A) is "..."')."""
    name: str                                   # "can't take what's already taken rule"
    routine: str                                # its routine in lib/i7/standard.zil
    responses: tuple[tuple[str, str], ...] = () # (letter, Inform 7 text) - the defaults
    needs: str = ""     # "parts" / "possessions": only in a story that has them


@dataclass(frozen=True)
class StandardAction:
    """One of Inform 7's standard actions, such as taking or putting it on."""
    name: str                                   # Inform 7's name: "putting it on"
    applying: int                               # things it applies to: 0, 1 or 2
    grammar: tuple[str, ...]                    # Understand lines
    rules: dict[str, tuple[LibraryRule, ...]] = field(default_factory=dict)
    out_of_world: bool = False                  # takes no time (saving, quitting)
    variables: str = ""                         # routine setting its action variables
    topic: bool = False                         # its last slot is a topic ([text])


# How to read an entry below:
#     StandardAction("taking", 1, ("take [things]", ...), {"check": (R(...), ...)})
# is the action's name, how many things it applies to, its grammar, and the
# library rules in each stage - each R(Inform 7 name, ZIL routine, responses).
R = LibraryRule
ACTIONS: tuple[StandardAction, ...] = (
    StandardAction("looking", 0, ("look", "l"), {"carry out": (
        R("room description heading rule", "LOOK-HEADING", (("A", "Darkness"),)),
        R("room description body text rule", "LOOK-BODY",
          (("A", "It is pitch dark, and you can't see a thing."),)),
        R("room description paragraphs about objects rule", "LOOK-OBJECTS"),
        R("check new arrival rule", "LOOK-NEW-ARRIVAL"))}),
    StandardAction("examining", 1,
                   ("examine [something]", "x [something]", "look at [something]",
                    "read [something]"), {"carry out": (
        R("standard examining rule", "EXAMINE-STANDARD"),
        R("examine undescribed things rule", "EXAMINE-UNDESCRIBED",
          (("A", "You see nothing special about [the noun]."),)))}),
    StandardAction("taking", 1, ("take [things]", "get [things]",       # Inform 7's grammar
                                 "pick up [things]", "pick [things] up"), {
        "check": (
            R("can't take yourself rule", "TAKE-YOURSELF",
              (("A", "You are always self-possessed."),)),
            R("can't take other people rule", "TAKE-PEOPLE",
              (("A", "I don't suppose [the noun] would care for that."),)),
            R("can't take component parts rule", "TAKE-PART",
              (("A", "[if the noun is plural-named]Those seem[otherwise]That seems[end if]"
                     " to be a part of [the holder of the noun]."),), needs="parts"),
             R("can't take people's possessions rule", "TAKE-POSSESSION",
               (("A", "[if the noun is plural-named]Those seem[otherwise]That seems[end if]"
                     " to belong to [the holder of the noun]."),), needs="possessions"),
            R("can't take what's already taken rule", "TAKE-ALREADY-TAKEN",
              (("A", "You already have that."),)),
            R("can't take scenery rule", "TAKE-SCENERY", (("A", "That's hardly portable."),)),
            R("can't take what's fixed in place rule", "TAKE-FIXED",
              (("A", "That's fixed in place."),))),
        "carry out": (R("standard taking rule", "TAKE-STANDARD"),),
        "report": (R("standard report taking rule", "TAKE-REPORT", (("A", "Taken."),)),)}),
    StandardAction("dropping", 1, ("drop [things preferably held]",
                                   "put down [things preferably held]",
                                   "discard [things preferably held]"), {
        "check": (R("can't drop what's already dropped rule", "DROP-ALREADY",
                    (("A", "[The noun] [are] already here."),)),
                  R("can't drop what's not held rule", "DROP-NOT-HELD",
                    (("A", "You haven't got that."),)),
                  R("can't drop clothes being worn rule", "TAKE-OFF-FIRST")),
        "carry out": (R("standard dropping rule", "DROP-STANDARD"),),
        "report": (R("standard report dropping rule", "DROP-REPORT", (("A", "Dropped."),)),)}),
    StandardAction("going", 1, (), {           # grammar: one line per direction (lower.py)
        "check": (
            R("can't go through closed doors rule", "GO-CLOSED-DOOR",
              (("A", "You can't, since [the door gone through] [are] closed."),)),
            R("can't go that way rule", "GO-THAT-WAY", (("A", "You can't go that way."),))),
        "carry out": (R("move player and vehicle rule", "GO-MOVE"),),
        "report": (R("describe room gone into rule", "GO-DESCRIBE"),)},
        variables="GOING-VARIABLES"),
    StandardAction("taking inventory", 0, ("inventory", "i", "inv"), {"carry out": (
        R("print empty inventory rule", "INVENTORY-EMPTY", (("A", "You are carrying nothing."),)),
        R("print standard inventory rule", "INVENTORY-STANDARD",
          (("A", "You are carrying:[line break]"),)))}),
    StandardAction("putting it on", 2, ("put [things preferably held] on [something]",
                                        "hang [things preferably held] on [something]"), {
        "check": (
            R("can't put something on itself rule", "PUT-ON-ITSELF",
              (("A", "You can't put something on top of itself."),)),
            R("can't put onto what's not a supporter rule", "PUT-NOT-SUPPORTER",
              (("A", "Putting things on [the second noun] would achieve nothing."),)),
            R("carrying requirements rule", "IMPLICITLY-TAKE"),
            R("can't put clothes being worn rule", "TAKE-OFF-FIRST")),
        "carry out": (R("standard putting rule", "PUT-STANDARD"),),
        "report": (R("standard report putting rule", "PUT-REPORT",
                     (("A", "You put [the noun] on [the second noun]."),)),)}),
    StandardAction("inserting it into", 2, ("put [things preferably held] in [something]",
                                            "insert [things preferably held] in [something]"), {
        "check": (
            R("can't insert something into itself rule", "INSERT-ITSELF",
              (("A", "You can't put something inside itself."),)),
            R("can't insert into what's not a container rule", "INSERT-NOT-CONTAINER",
              (("A", "[The second noun] can't contain things."),)),
            R("can't insert into closed containers rule", "INSERT-CLOSED",
              (("A", "[The second noun] [are] closed."),)),
            R("carrying requirements rule", "IMPLICITLY-TAKE"),
            R("can't insert clothes being worn rule", "TAKE-OFF-FIRST")),
        "carry out": (R("standard inserting rule", "INSERT-STANDARD"),),
        "report": (R("standard report inserting rule", "INSERT-REPORT",
                     (("A", "You put [the noun] into [the second noun]."),)),)}),
    StandardAction("wearing", 1, ("wear [something]", "put on [something]",
                                  "don [something]"), {
        "check": (
            R("can't wear what's not clothing rule", "WEAR-NOT-CLOTHING",
              (("A", "You can't wear that!"),)),
            R("can't wear what's already worn rule", "WEAR-ALREADY",
              (("A", "You're already wearing that!"),)),
            R("carrying requirements rule", "IMPLICITLY-TAKE")),
        "carry out": (R("standard wearing rule", "WEAR-STANDARD"),),
        "report": (R("standard report wearing rule", "WEAR-REPORT",
                     (("A", "You put on [the noun]."),)),)}),
    StandardAction("taking off", 1, ("take off [something]", "remove [something]",
                                     "doff [something]"), {
        "check": (R("can't take off what's not worn rule", "TAKE-OFF-NOT-WORN",
                    (("A", "You're not wearing that."),)),),
        "carry out": (R("standard taking off rule", "TAKE-OFF-STANDARD"),),
        "report": (R("standard report taking off rule", "TAKE-OFF-REPORT",
                     (("A", "You take off [the noun]."),)),)}),
    StandardAction("opening", 1, ("open [something]",), {
        "check": (
            R("can't open unless openable rule", "OPEN-UNOPENABLE",
              (("A", "That's not something you can open."),)),
            R("can't open what's locked rule", "OPEN-LOCKED", (("A", "It seems to be locked."),)),
            R("can't open what's already open rule", "OPEN-ALREADY",
              (("A", "That's already open."),))),
        "carry out": (R("standard opening rule", "OPEN-STANDARD"),),
        "report": (R("reveal any newly visible interior rule", "OPEN-REVEAL",
                     (("A", "You open [the noun], revealing "),)),        # ADR-057
                   R("standard report opening rule", "OPEN-REPORT",
                     (("A", "You open [the noun]."),)),)}),
    StandardAction("closing", 1, ("close [something]", "shut [something]"), {
        "check": (
            R("can't close unless openable rule", "CLOSE-UNOPENABLE",
              (("A", "That's not something you can close."),)),
            R("can't close what's already closed rule", "CLOSE-ALREADY",
              (("A", "That's already closed."),))),
        "carry out": (R("standard closing rule", "CLOSE-STANDARD"),),
        "report": (R("standard report closing rule", "CLOSE-REPORT",
                     (("A", "You close [the noun]."),)),)}),
    StandardAction("locking it with", 2, ("lock [something] with [something]",), {
        "check": (
            R("can't lock without a lock rule", "LOCK-NO-LOCK",
              (("A", "That doesn't seem to be something you can lock."),)),
            R("can't lock what's already locked rule", "LOCK-ALREADY",
              (("A", "It's locked at the moment."),)),
            R("can't lock what's open rule", "LOCK-OPEN",
              (("A", "First you would have to close [the noun]."),)),
            R("can't lock without the correct key rule", "LOCK-WRONG-KEY",
              (("A", "That doesn't seem to fit the lock."),))),
        "carry out": (R("standard locking rule", "LOCK-STANDARD"),),
        "report": (R("standard report locking rule", "LOCK-REPORT",
                     (("A", "You lock [the noun]."),)),)}),
    StandardAction("unlocking it with", 2, ("unlock [something] with [something]",
                                            "open [something] with [something]"), {
        "check": (
            R("can't unlock without a lock rule", "UNLOCK-NO-LOCK",
              (("A", "That doesn't seem to be something you can unlock."),)),
            R("can't unlock what's already unlocked rule", "UNLOCK-ALREADY",
              (("A", "It's unlocked at the moment."),)),
            R("can't unlock without the correct key rule", "UNLOCK-WRONG-KEY",
              (("A", "That doesn't seem to fit the lock."),))),
        "carry out": (R("standard unlocking rule", "UNLOCK-STANDARD"),),
        "report": (R("standard report unlocking rule", "UNLOCK-REPORT",
                     (("A", "You unlock [the noun]."),)),)}),
    StandardAction("switching on", 1, ("switch on [something]", "turn on [something]",
                                       "switch [something] on", "turn [something] on"), {
        "check": (
            R("can't switch on unless switchable rule", "SWITCH-ON-UNSWITCHABLE",
              (("A", "That isn't something you can switch."),)),
            R("can't switch on what's already on rule", "SWITCH-ON-ALREADY",
              (("A", "That's already on."),))),
        "carry out": (R("standard switching on rule", "SWITCH-ON-STANDARD"),),
        "report": (R("standard report switching on rule", "SWITCH-ON-REPORT",
                     (("A", "You switch [the noun] on."),)),)}),
    StandardAction("switching off", 1, ("switch off [something]", "turn off [something]",
                                        "switch [something] off", "turn [something] off"), {
        "check": (
            R("can't switch off unless switchable rule", "SWITCH-OFF-UNSWITCHABLE",
              (("A", "That isn't something you can switch."),)),
            R("can't switch off what's already off rule", "SWITCH-OFF-ALREADY",
              (("A", "That's already off."),))),
        "carry out": (R("standard switching off rule", "SWITCH-OFF-STANDARD"),),
        "report": (R("standard report switching off rule", "SWITCH-OFF-REPORT",
                     (("A", "You switch [the noun] off."),)),)}),
    # The four actions on a topic: the words typed as [text] (docs/TOPICS_PLAN.md).
    # 'applying' counts the topic's slot as well as the thing's.
    StandardAction("consulting it about", 2,
                   ("consult [something] on/about [text]", "look up [text] in [something]",
                    "read about [text] in [something]"), {"report": (
        R("block consulting rule", "CONSULT-BLOCK",
          (("A", "You discover nothing of interest in [the noun]."),)),)}, topic=True),
    StandardAction("asking it about", 2, ("ask [someone] about [text]",), {"check": (
        R("block asking rule", "ASK-BLOCK", (("A", "There is no reply."),)),)}, topic=True),
    StandardAction("telling it about", 2, ("tell [someone] about [text]",), {"check": (
        R("telling yourself rule", "TELL-YOURSELF",
          (("A", "You talk to yourself a while."),)),
        R("block telling rule", "TELL-BLOCK", (("A", "This provokes no reaction."),)))},
        topic=True),
    StandardAction("answering it that", 2,
                   ("answer [text] to [someone]", "say [text] to [someone]",
                    "shout [text] to [someone]", "speak [text] to [someone]"), {"check": (
        R("block answering rule", "ANSWER-BLOCK", (("A", "There is no reply."),)),)},
        topic=True),
    # Words and replies as the real library gives them (checked against Cold
    # Iron, built by Inform 7). I7-lite has no enterable things, so entering is
    # always refused; Inform's one response adapts to the verb, here A/B/C.
    StandardAction("attacking", 1,
                   ("attack [something]", "break [something]", "smash [something]",
                    "hit [something]", "punch [something]", "destroy [something]",
                    "thump [something]"), {"check": (
        R("block attacking rule", "ATTACK-BLOCK",
          (("A", "Violence isn't the answer to this one."),)),)}),
    StandardAction("entering", 1,
                   ("enter [something]", "get in/into/on/onto [something]",
                    "sit on/in/inside [something]", "stand on [something]"), {"check": (
        R("can't enter what's not enterable rule", "ENTER-NOT-ENTERABLE",
          (("A", "That's not something you can enter."),
           ("B", "That's not something you can sit down on."),
           ("C", "That's not something you can stand on."))),)}),
    # ADR-058: twelve more of Inform's standard actions. Replies as the real *The
    # Ambassador's Daughter* (Inform 6G60) prints them, where it could be checked.
    StandardAction("searching", 1, ("search [something]", "look in/inside/into [something]"), {
        "check": (
            R("can't search unless container or supporter rule", "SEARCH-NOT-CS",
              (("A", "You find nothing of interest."),)),
            R("can't search closed opaque containers rule", "SEARCH-CLOSED",
              (("A", "You can't see inside, since [the noun] [if the noun is "
                     "plural-named]are[otherwise]is[end if] closed."),))),
        "report": (
            R("standard search containers rule", "SEARCH-CONTAINER",
              (("A", "In [the noun] "),
               ("B", "[The noun] [if the noun is plural-named]are[otherwise]is[end if] empty."))),
            R("standard search supporters rule", "SEARCH-SUPPORTER",
              (("A", "On [the noun] "), ("B", "There is nothing on [the noun]."))))}),
    StandardAction("touching", 1, ("touch [something]", "feel [something]",
                                   "fondle [something]", "grope [something]"), {"report": (
        R("report touching yourself rule", "TOUCH-SELF", (("A", "If you think that'll help."),)),
        R("report touching other people rule", "TOUCH-PEOPLE",
          (("A", "[The noun] might not like that."),)),
        R("report touching things rule", "TOUCH-THINGS",
          (("A", "You feel nothing unexpected."),)))}),
    StandardAction("climbing", 1, ("climb [something]", "scale [something]",
                                   "climb up/over [something]"), {"check": (
        R("block climbing rule", "CLIMB-BLOCK",
          (("A", "I don't think much is to be achieved by that."),)),)}),
    StandardAction("giving it to", 2, ("give [something] to [someone]",
                                       "pay [something] to [someone]",
                                       "offer [something] to [someone]",
                                       "feed [something] to [someone]"), {"check": (
        R("carrying requirements rule", "IMPLICITLY-TAKE"),
        R("can't give to yourself rule", "GIVE-SELF",
          (("A", "You can't give [the noun] to yourself."),)),
        R("can't give to a non-person rule", "GIVE-NONPERSON",
          (("A", "[The second noun] [if the second noun is "
                 "plural-named]aren't[otherwise]isn't[end if] able to receive things."),)),
        R("block giving rule", "GIVE-BLOCK",
          (("A", "[The second noun] [if the second noun is "
                 "plural-named]don't[otherwise]doesn't[end if] seem interested."),)))}),
    StandardAction("showing it to", 2, ("show [something] to [someone]",
                                        "present [something] to [someone]",
                                        "display [something] to [someone]"), {"check": (
        R("carrying requirements rule", "IMPLICITLY-TAKE"),
        R("block showing rule", "SHOW-BLOCK",
          (("A", "[The second noun] [if the second noun is "
                 "plural-named]are[otherwise]is[end if] unimpressed."),)))}),
    StandardAction("exiting", 0, ("exit", "out", "get out", "stand up"), {"check": (
        R("convert exit into go out rule", "EXIT-GO-OUT"),
        R("can't exit when not inside anything rule", "EXIT-NOT-INSIDE",
          (("A", "But you aren't in anything at the moment."),)))}),
    StandardAction("drinking", 1, ("drink [something]", "swallow [something]",
                                   "sip [something]"), {"check": (
        R("block drinking rule", "DRINK-BLOCK",
          (("A", "There's nothing suitable to drink here."),)),)}),
    StandardAction("sleeping", 0, ("sleep", "nap"), {"check": (
        R("block sleeping rule", "SLEEP-BLOCK",
          (("A", "You aren't feeling especially drowsy."),)),)}),
    StandardAction("tasting", 1, ("taste [something]",), {"check": (
        R("block tasting rule", "TASTE-BLOCK", (("A", "You taste nothing unexpected."),)),)}),
    StandardAction("rubbing", 1, ("rub [something]", "shine [something]", "polish [something]",
                                  "sweep [something]", "clean [something]", "dust [something]",
                                  "wipe [something]", "scrub [something]"), {"check": (
        R("can't rub another person rule", "RUB-PEOPLE",
          (("A", "[The noun] might not like that."),)),
        R("block rubbing rule", "RUB-BLOCK", (("A", "You achieve nothing by this."),)))}),
    StandardAction("pushing", 1, ("push [something]", "press [something]", "shift [something]"), {
        "check": (
            R("can't push what's fixed in place rule", "PUSH-FIXED",
              (("A", "[if the noun is plural-named]Those are[otherwise]It is[end if] fixed "
                     "in place."),)),
            R("can't push people rule", "PUSH-PEOPLE",
              (("A", "[The noun] might not like that."),))),
        "report": (R("report pushing rule", "PUSH-REPORT", (("A", "Nothing obvious "
                                                                  "happens."),)),)}),
    StandardAction("turning", 1, ("turn [something]", "rotate [something]", "twist [something]",
                                  "unscrew [something]", "screw [something]"), {
        "check": (
            R("can't turn what's fixed in place rule", "TURN-FIXED",
              (("A", "[if the noun is plural-named]Those are[otherwise]It is[end if] fixed "
                     "in place."),)),
            R("can't turn people rule", "TURN-PEOPLE",
              (("A", "[The noun] might not like that."),))),
        "report": (R("report turning rule", "TURN-REPORT", (("A", "Nothing obvious "
                                                                  "happens."),)),)}),
    StandardAction("waiting", 0, ("wait", "z"), {"report": (
        R("standard report waiting rule", "WAIT-REPORT", (("A", "Time passes."),)),)}),
    StandardAction("requesting the score", 0, ("score",),
                   {"carry out": (R("announce the score rule", "SCORE-ANNOUNCE"),)},
                   out_of_world=True),
    StandardAction("saving the game", 0, ("save",),
                   {"carry out": (R("save the game rule", "SAVE-GAME"),)}, out_of_world=True),
    StandardAction("restoring the game", 0, ("restore",),
                   {"carry out": (R("restore the game rule", "RESTORE-GAME"),)},
                   out_of_world=True),
    StandardAction("quitting the game", 0, ("quit", "q"),
                   {"carry out": (R("quit the game rule", "QUIT-GAME"),)}, out_of_world=True),
)

# Inform 7's testing commands. Inform leaves them out of a released game;
# zforge adds them only when asked ('zforge compile --testing'), so an
# ordinary build is exactly what it was. Routines: lib/i7/testing.zil.
TESTING_ACTIONS: tuple[StandardAction, ...] = (
    StandardAction("switching rules tracing on", 0, ("rules", "rules on"),
                   {"carry out": (R("rules tracing on rule", "RULES-ON"),)}, out_of_world=True),
    StandardAction("switching rules tracing off", 0, ("rules off",),
                   {"carry out": (R("rules tracing off rule", "RULES-OFF"),)}, out_of_world=True),
    StandardAction("switching actions listing on", 0, ("actions", "actions on"),
                   {"carry out": (R("actions listing on rule", "ACTIONS-ON"),)},
                   out_of_world=True),
    StandardAction("switching actions listing off", 0, ("actions off",),
                   {"carry out": (R("actions listing off rule", "ACTIONS-OFF"),)},
                   out_of_world=True),
    StandardAction("showing the object tree", 0, ("tree",),
                   {"carry out": (R("object tree rule", "SHOW-TREE"),)}, out_of_world=True),
)
del R

# Every library rule by its Inform 7 name (a rule such as the carrying
# requirements rule appears in several rulebooks: same routine, same name).
# Rules that belong to no rulebook: the library calls them itself, and an
# author may only edit their responses.  The list writer annotates each
# line of an inventory: "a lamp (providing light)", "a cloak (being worn)".
INTERNAL_RULES: tuple[LibraryRule, ...] = (
    LibraryRule("list writer internal rule", "LIST-WRITER",
                (("D", "providing light"), ("E", "closed"), ("F", "empty"),
                 ("H", "closed and providing light"), ("I", "empty and providing light"),
                 ("K", "providing light and being worn"), ("L", "being worn"),
                 ("R", "on which "), ("T", "in which "))),       # ADR-057
    # 'if the player consents' asks again: Advent edits it (source line 397)
    LibraryRule("yes or no question internal rule", "YES-OR-NO",
                (("A", "Please answer yes or no."),)),
)

LIBRARY_RULES: dict[str, LibraryRule] = {
    rule.name: rule for action in ACTIONS for stage in action.rules.values() for rule in stage}
LIBRARY_RULES.update({rule.name: rule for rule in INTERNAL_RULES})


@dataclass(frozen=True)
class LibraryActivity:
    """One of Inform 7's activities that the library carries out (activities.zil).

    name        how an author refers to it: "Rule for printing the name of ..."
    atom        the ZIL global holding its three rulebooks (before, for, after)
    preposition "of" / "about" when the activity is about an object (the
                item described), "" when it is about nothing
    """
    name: str
    atom: str
    preposition: str = ""


# Longest names first, so "printing the name of a dark room" is not read as
# "printing the name" of an object called "a dark room".
ACTIVITIES: tuple[LibraryActivity, ...] = (
    LibraryActivity("printing the description of a dark room", "PRINTING-DARK-DESC-ACTIVITY"),
    LibraryActivity("printing the name of a dark room", "PRINTING-DARK-NAME-ACTIVITY"),
    LibraryActivity("printing the banner text", "PRINTING-BANNER-ACTIVITY"),
    LibraryActivity("printing a parser error", "PRINTING-PARSER-ERROR-ACTIVITY"),
    LibraryActivity("printing the name", "PRINTING-NAME-ACTIVITY", "of"),
    LibraryActivity("writing a paragraph", "WRITING-PARAGRAPH-ACTIVITY", "about"),
)

# Inform 7's parser errors, by the names an author uses ('the latest parser
# error is the can't see any such thing error'). The names are Inform 7's own
# (checked against the compiled Advent_Crowther.z8, which contains them).
# I7-lite's parser makes the first eight; a rule about any other can be written
# but never applies - as in a game where that kind of mistake cannot happen.
PARSER_ERRORS: dict[str, str] = {
    "didn't understand": "PE-DIDNT-UNDERSTAND",
    "can't see any such thing": "PE-CANT-SEE",
    "not sure what it refers to": "PE-NOT-SURE",
    "can't see it at the moment": "PE-CANT-SEE-IT",
    "not a verb i recognise": "PE-NOT-A-VERB",
    "i beg your pardon": "PE-PARDON",
    "can't use multiple objects": "PE-CANT-USE-MULTIPLE",
    "nothing to do": "PE-NOTHING-TO-DO",
    # never made by I7-lite's parser: each has its own number (101 up),
    # which LATEST-PARSER-ERROR never holds
    "only understood as far as": "101",
    "didn't understand that number": "102",
    "said too little": "103",
    "aren't holding that": "104",
    "can only use multiple objects": "106",
    "excepted something not included": "107",
    "can only do that to something animate": "108",
    "not something you need to refer to": "109",
    "didn't understand the way that finished": "110",
    "not enough of those available": "111",
    "noun did not make sense in that context": "113",
    "referred to a determination of scope": "114",
    "can't again the addressee": "115",
    "comma can't begin": "116",
    "can't see whom to talk to": "117",
    "can't talk to inanimate things": "118",
    "didn't understand addressee's last name": "119",
}


# Inform 7 activities that I7-lite knows by name but does not carry out yet:
# a rule for one gets a clear problem instead of being read as an action.
UNSUPPORTED_ACTIVITIES: tuple[str, ...] = (
    "printing the announcement of darkness", "printing the announcement of light",
    "supplying a missing noun", "supplying a missing second noun",
    "choosing notable locale objects", "printing the locale description",
    "printing a locale paragraph about", "listing contents", "listing nondescript items",
    "grouping together", "printing the plural name", "printing room description details",
    "printing inventory details", "printing a refusal to act in the dark",
    "printing the player's obituary", "amusing a victorious player",
    "handling the final question", "deciding the scope", "deciding the concealed possessions",
    "deciding whether all includes", "clarifying the parser's choice", "asking which do you mean",
    "reading a command", "implicitly taking", "constructing the status line",
    "starting the virtual machine", "printing a number", "issuing the response text",
)


# (name, abbreviation, opposite): the twelve Inform 7 directions.
DIRECTIONS: tuple[tuple[str, str, str], ...] = (
    ("north", "n", "south"), ("northeast", "ne", "southwest"),
    ("east", "e", "west"), ("southeast", "se", "northwest"),
    ("south", "s", "north"), ("southwest", "sw", "northeast"),
    ("west", "w", "east"), ("northwest", "nw", "southeast"),
    ("up", "u", "down"), ("down", "d", "up"),
    ("inside", "in", "outside"), ("outside", "out", "inside"),
)
# 'The Hall is north of the Kitchen' also makes the Kitchen south of the Hall.
OPPOSITE = {name: opposite for name, _, opposite in DIRECTIONS}


def zil_string(s: str) -> str:
    """A ZIL string literal. A line break in the source text, with the spaces
    around it, becomes one space (as in Inform 7); other spaces are kept
    ('...instructions?[paragraph break]  ' prompts with two). '|' is ZIL's
    newline, so it is avoided."""
    s = re.sub(r"[ \t]*\n\s*", " ", s).replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("|", "/")
    return f'"{s}"'


def zil_name(words: str) -> str:
    """Inform 7 name -> ZIL atom: 'putting it on' -> PUTTING-IT-ON."""
    cleaned = "".join(ch if ch.isalnum() else " " for ch in words)
    return "-".join(cleaned.upper().split())
