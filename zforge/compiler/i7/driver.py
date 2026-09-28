"""compile_i7: Inform 7 (I7-lite) source -> ZIL-lite text -> story file.

    source.py   sentences and rule bodies
    model.py    the world model (two passes, so forward references work)
    lower.py    ZIL-lite text, using lib/i7/*.zil at run time
    ...then zforge's ZIL-lite compiler does the rest.

If the ZIL compiler rejects the generated code, that is a bug in I7-lite
(not in the author's source): the error says so, with the generated file."""

from __future__ import annotations

import re

from dataclasses import dataclass
from pathlib import Path

from zforge.common.errors import ZForgeError
from zforge.compiler.driver import CompileResult, compile_zil
from zforge.compiler.i7.lower import lower_model
from zforge.compiler.i7.model import WorldModel, build_model
from zforge.compiler.i7.problems import Problems
from zforge.compiler.i7.source import read_sentences

DEFAULT_TARGET = 8          # I7-lite stories default to z8 (proforma; ADR-025)


@dataclass
class I7Result:
    """Everything one compile produced: the model, the ZIL, the story, notes."""
    model: WorldModel
    zil: str                # the generated ZIL-lite source
    compiled: CompileResult
    notes: list[str]

    @property
    def story(self) -> bytes:
        """The finished story file's bytes."""
        return self.compiled.story

    @property
    def version(self) -> int:
        """The Z-machine version it was built for (5, 6, 7 or 8)."""
        return self.compiled.version


def generate_zil(source: str, filename: str = "story.ni",
                 testing: bool = False) -> tuple[WorldModel, str, list[str]]:
    """The first half: I7 text -> (model, ZIL-lite text, notes). TESTING adds
    Inform's testing commands (RULES, ACTIONS, TREE)."""
    problems = Problems(Path(filename).name)
    model = build_model(read_sentences(source), problems, testing)
    bare = re.sub(r'"[^"]*"|\[[^\]]*\]', "", source)      # no quoted texts, no comments
    model.uses_parts = model.uses_parts or bool(re.search(r"\bpart of\b", bare, re.I))
    model.uses_times = bool(re.search(r"\b\d{1,2}:\d\d\b|\bhas an? time\b", bare, re.I)
                            or "[time]" in source)
    problems.raise_if_any()                        # no point lowering a broken model
    zil = lower_model(model, problems, Path(filename).with_suffix(".zil").name)
    problems.raise_if_any()
    return model, zil, model.notes


def compile_i7(source: str, filename: str = "story.ni", target: int | None = None,
               testing: bool = False) -> I7Result:
    """Compile Inform 7 source all the way to a story file (the public entry point).

    TARGET is the Z-machine version (default 8); TESTING adds RULES, ACTIONS and
    TREE. Problems in the source raise with Inform-style messages."""
    model, zil, notes = generate_zil(source, filename, testing)
    # The second half: hand the generated ZIL to the ordinary ZIL compiler.
    generated = str(Path(filename).with_suffix(".generated.zil"))
    try:
        compiled = compile_zil(zil, generated, target if target is not None else DEFAULT_TARGET)
    except ZForgeError as e:
        if "too many FLAGS" in str(e):
            report_too_many_attributes(model, filename, str(e))
        raise ZForgeError("internal error: I7-lite generated ZIL that does not compile "
                          "(a bug in zforge, not in your source; see it with --emit-zil):"
                          f"\n{e}") from e
    return I7Result(model, zil, compiled, notes)


def report_too_many_attributes(model: WorldModel, filename: str, message: str) -> None:
    """Every either/or property ('A thing can be shiny') becomes a Z-machine
    attribute, and there are only 48 of them, shared with the library. That is
    a limit of the story, not a zforge bug, so say so as an Inform-style
    problem, pointing at the first of the story's own properties that did not
    fit."""
    used = re.search(r"uses (\d+) attributes", message)
    unplaced = re.search(r"Not allocated: (.*)", message)
    flags = [f.strip() for f in unplaced.group(1).split(",")] if unplaced else []
    names = {flag: adj for adj, (flag, value) in model.either_or.items() if value}
    mine = [f for f in flags if f in model.either_or_where]
    problems = Problems(Path(filename).name)
    where, sentence = (model.either_or_where[mine[0]] if mine
                       else next(iter(model.either_or_where.values())))
    problems.problem(where, sentence, (
        f"that makes {used.group(1) if used else 'more than 48'} either/or properties "
        "in all, counting the ones the library uses itself, and the Z-machine has room "
        "for only 48 (§12.3.1). "
        + (f"The ones that did not fit: {', '.join(names.get(f, f) for f in flags)}. "
           if flags else "")
        + "Try turning a group of them into one number property (a room can have a "
        "number called its wing, say, instead of being central, ancient or "
        "residential), or removing ones that no rule ever tests."))
    problems.raise_if_any()
