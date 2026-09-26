"""Glue: run the compiler stages in order and stop at the first stage
that reported errors (so later stages never see a broken tree)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from zforge.asm.assembler import assemble
from zforge.compiler.codegen import CodeGenerator
from zforge.compiler.diagnostics import CompileError, Diagnostics
from zforge.compiler.forms import FormParser
from zforge.compiler.grammar import desugar
from zforge.compiler.lexer import Lexer
from zforge.compiler.reader import read
from zforge.compiler.semantic import analyse
from zforge.common.versions import profile_for, supported_versions


def read_source(source: str, diag: Diagnostics) -> list:
    return read(Lexer(source, diag).tokens(), diag)


@dataclass
class CompileResult:
    tokens: list
    data: list
    program: object
    assembly: str
    story: bytes
    version: int = 5


def compatible_targets(declared: int) -> list[int]:
    """The versions a source written for `declared` can be built for: those
    with the same opcode set. §1: "Versions 7 and 8 are identical to Version
    5 except as stated at 1.1.4 and 1.2.3" (size and packed addresses, which
    the assembler handles), so a v5 source builds for 5, 7 and 8."""
    table = profile_for(declared).opcode_table
    return [v for v in supported_versions() if profile_for(v).opcode_table == table]


def compile_zil(source: str, filename: str = "<zil>", target: int | None = None) -> CompileResult:
    """Compile ZIL-lite. `target` overrides the source's <VERSION> (see
    compatible_targets); None builds the version the source declares."""
    diag = Diagnostics(filename, source)
    tokens = Lexer(source, diag).tokens()
    data = read(tokens, diag)
    program = FormParser(diag, Path(filename).parent).parse_program(data)
    desugar(program, diag)           # SYNTAX lines -> constants + SYNTAX-TABLE
    # Semantic checks run even after syntax errors (the AST is still well
    # formed), so one run reports as many problems as possible.
    symbols = analyse(program, diag)
    version = target if target is not None else program.version
    if version not in compatible_targets(program.version):
        allowed = ", ".join(f"z{v}" for v in compatible_targets(program.version))
        diag.error(tokens[0].location,           # the problem is the whole file
                   f"this source is written for version {program.version}; it can be built "
                   f"for {allowed}, not z{version}")
    if diag:
        raise CompileError(diag)
    assembly = CodeGenerator(program, symbols, diag, filename).generate()
    if diag:
        raise CompileError(diag)
    story = assemble(assembly, filename + " (generated .zas)", version)
    return CompileResult(tokens, data, program, assembly, story, version)
