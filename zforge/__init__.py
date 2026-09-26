"""zforge - a readable Z-machine version 5 toolchain.

    zforge.common    shared pieces: memory, header, text (z-strings), opcode table
    zforge.vm        the interpreter (decoder, CPU, opcodes, objects, screens)
    zforge.asm       assembler, story-file linker, disassembler
    zforge.compiler  ZIL-lite compiler: lexer -> reader -> AST -> codegen -> .zas
    zforge.cli       the `zforge` command

Every module names the section of the Z-Machine Standard 1.1 it implements
as "§n.m". Start reading at docs/01-zmachine-tour.md.
"""
__version__ = "0.1.0"
