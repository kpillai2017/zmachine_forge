"""compile_i7: Inform 7 (I7-lite) source -> ZIL-lite text -> story file.

    source.py   sentences and rule bodies
    model.py    the world model (two passes, so forward references work)
    lower.py    ZIL-lite text, using lib/i7/*.zil at run time
    ...then zforge's ZIL-lite compiler does the rest.

If the ZIL compiler rejects the generated code, that is a bug in I7-lite
(not in the author's source): the error says so, with the generated file."""

from __future__ import annotations

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
    model: WorldModel
    zil: str                # the generated ZIL-lite source
    compiled: CompileResult
    notes: list[str]

    @property
    def story(self) -> bytes:
        return self.compiled.story

    @property
    def version(self) -> int:
        return self.compiled.version


def generate_zil(source: str, filename: str = "story.ni") -> tuple[WorldModel, str, list[str]]:
    """The first half: I7 text -> (model, ZIL-lite text, notes)."""
    problems = Problems(Path(filename).name)
    model = build_model(read_sentences(source), problems)
    problems.raise_if_any()                        # no point lowering a broken model
    zil = lower_model(model, problems, Path(filename).with_suffix(".zil").name)
    problems.raise_if_any()
    return model, zil, model.notes


def compile_i7(source: str, filename: str = "story.ni", target: int | None = None) -> I7Result:
    model, zil, notes = generate_zil(source, filename)
    generated = str(Path(filename).with_suffix(".generated.zil"))
    try:
        compiled = compile_zil(zil, generated, target if target is not None else DEFAULT_TARGET)
    except ZForgeError as e:
        raise ZForgeError("internal error: I7-lite generated ZIL that does not compile "
                          "(a bug in zforge, not in your source; see it with --emit-zil):"
                          f"\n{e}") from e
    return I7Result(model, zil, compiled, notes)
