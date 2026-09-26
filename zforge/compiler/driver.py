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


def read_source(source: str, diag: Diagnostics) -> list:
    return read(Lexer(source, diag).tokens(), diag)


@dataclass
class CompileResult:
    tokens: list
    data: list
    program: object
    assembly: str
    story: bytes


def compile_zil(source: str, filename: str = "<zil>") -> CompileResult:
    diag = Diagnostics(filename, source)
    tokens = Lexer(source, diag).tokens()
    data = read(tokens, diag)
    program = FormParser(diag, Path(filename).parent).parse_program(data)
    desugar(program, diag)           # SYNTAX lines -> constants + SYNTAX-TABLE
    # Semantic checks run even after syntax errors (the AST is still well
    # formed), so one run reports as many problems as possible.
    symbols = analyse(program, diag)
    if diag:
        raise CompileError(diag)
    assembly = CodeGenerator(program, symbols, diag, filename).generate()
    if diag:
        raise CompileError(diag)
    story = assemble(assembly, filename + " (generated .zas)")
    return CompileResult(tokens, data, program, assembly, story)
