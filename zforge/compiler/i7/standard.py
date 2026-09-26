"""The standard actions and directions: I7-lite's small 'Standard Rules'.

Each standard action lists its Inform 7 name, how many things it applies
to, its grammar (written as Inform 7 Understand lines, compiled exactly
like an author's), and the library rule routines (zforge/lib/i7/
standard.zil) that go into each stage of its rulebook."""

from __future__ import annotations

from dataclasses import dataclass, field

STAGES = ("before", "instead", "check", "carry out", "after", "report")


@dataclass(frozen=True)
class StandardAction:
    name: str                                   # Inform 7's name: "putting it on"
    applying: int                               # things it applies to: 0, 1 or 2
    grammar: tuple[str, ...]                    # Understand lines
    rules: dict[str, tuple[str, ...]] = field(default_factory=dict)
    out_of_world: bool = False                  # takes no time (saving, quitting)


ACTIONS: tuple[StandardAction, ...] = (
    StandardAction("looking", 0, ("look", "l"), {"carry out": ("LOOKING-CARRY-OUT",)}),
    StandardAction("examining", 1,
                   ("examine [something]", "x [something]", "look at [something]",
                    "read [something]"),
                   {"carry out": ("EXAMINING-CARRY-OUT",)}),
    StandardAction("taking", 1, ("take [something]", "get [something]",
                                 "pick up [something]", "pick [something] up"),
                   {"check": ("TAKING-CHECK",), "carry out": ("TAKING-CARRY-OUT",),
                    "report": ("TAKING-REPORT",)}),
    StandardAction("dropping", 1, ("drop [something]", "put down [something]",
                                   "discard [something]"),
                   {"check": ("DROPPING-CHECK",), "carry out": ("DROPPING-CARRY-OUT",),
                    "report": ("DROPPING-REPORT",)}),
    StandardAction("going", 1, (),           # grammar: one line per direction (lower.py)
                   {"check": ("GOING-CHECK",), "carry out": ("GOING-CARRY-OUT",),
                    "report": ("GOING-REPORT",)}),
    StandardAction("taking inventory", 0, ("inventory", "i", "inv"),
                   {"carry out": ("INVENTORY-CARRY-OUT",)}),
    StandardAction("putting it on", 2, ("put [something] on [something]",
                                        "hang [something] on [something]"),
                   {"check": ("PUTTING-CHECK",), "carry out": ("PUTTING-CARRY-OUT",),
                    "report": ("PUTTING-REPORT",)}),
    StandardAction("inserting it into", 2, ("put [something] in [something]",
                                            "insert [something] in [something]"),
                   {"check": ("INSERTING-CHECK",), "carry out": ("INSERTING-CARRY-OUT",),
                    "report": ("INSERTING-REPORT",)}),
    StandardAction("wearing", 1, ("wear [something]", "put on [something]",
                                  "don [something]"),
                   {"check": ("WEARING-CHECK",), "carry out": ("WEARING-CARRY-OUT",),
                    "report": ("WEARING-REPORT",)}),
    StandardAction("taking off", 1, ("take off [something]", "remove [something]",
                                     "doff [something]"),
                   {"check": ("TAKING-OFF-CHECK",), "carry out": ("TAKING-OFF-CARRY-OUT",),
                    "report": ("TAKING-OFF-REPORT",)}),
    StandardAction("opening", 1, ("open [something]",),
                   {"check": ("OPENING-CHECK",), "carry out": ("OPENING-CARRY-OUT",),
                    "report": ("OPENING-REPORT",)}),
    StandardAction("closing", 1, ("close [something]", "shut [something]"),
                   {"check": ("CLOSING-CHECK",), "carry out": ("CLOSING-CARRY-OUT",),
                    "report": ("CLOSING-REPORT",)}),
    StandardAction("locking it with", 2, ("lock [something] with [something]",),
                   {"check": ("LOCKING-CHECK",), "carry out": ("LOCKING-CARRY-OUT",),
                    "report": ("LOCKING-REPORT",)}),
    StandardAction("unlocking it with", 2, ("unlock [something] with [something]",
                                            "open [something] with [something]"),
                   {"check": ("UNLOCKING-CHECK",), "carry out": ("UNLOCKING-CARRY-OUT",),
                    "report": ("UNLOCKING-REPORT",)}),
    StandardAction("switching on", 1, ("switch on [something]", "turn on [something]",
                                       "switch [something] on", "turn [something] on"),
                   {"check": ("SWITCHING-ON-CHECK",), "carry out": ("SWITCHING-ON-CARRY-OUT",),
                    "report": ("SWITCHING-ON-REPORT",)}),
    StandardAction("switching off", 1, ("switch off [something]", "turn off [something]",
                                        "switch [something] off", "turn [something] off"),
                   {"check": ("SWITCHING-OFF-CHECK",),
                    "carry out": ("SWITCHING-OFF-CARRY-OUT",),
                    "report": ("SWITCHING-OFF-REPORT",)}),
    StandardAction("waiting", 0, ("wait", "z"), {"report": ("WAITING-REPORT",)}),
    StandardAction("requesting the score", 0, ("score",),
                   {"carry out": ("SCORE-CARRY-OUT",)}, out_of_world=True),
    StandardAction("saving the game", 0, ("save",),
                   {"carry out": ("SAVING-CARRY-OUT",)}, out_of_world=True),
    StandardAction("restoring the game", 0, ("restore",),
                   {"carry out": ("RESTORING-CARRY-OUT",)}, out_of_world=True),
    StandardAction("quitting the game", 0, ("quit", "q"),
                   {"carry out": ("QUITTING-CARRY-OUT",)}, out_of_world=True),
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
OPPOSITE = {name: opposite for name, _, opposite in DIRECTIONS}


def zil_name(words: str) -> str:
    """Inform 7 name -> ZIL atom: 'putting it on' -> PUTTING-IT-ON."""
    cleaned = "".join(ch if ch.isalnum() else " " for ch in words)
    return "-".join(cleaned.upper().split())
