"""zforge - a readable Z-machine toolchain: versions 5, 6, 7 and 8.

    zforge.common       shared pieces: memory, header, text (z-strings), opcode
                        table, version rules, Blorb files
    zforge.vm           the interpreter (decoder, CPU, opcodes, objects, screens)
    zforge.asm          assembler, story-file linker, disassembler
    zforge.compiler     ZIL-lite compiler: lexer -> reader -> AST -> codegen -> .zas
    zforge.compiler.i7  I7-lite compiler: Inform 7 sentences -> world model -> ZIL-lite
    zforge.cli          the `zforge` command

Every module names the section of the Z-Machine Standard 1.1 it implements
as "§n.m". Start reading at docs/TOUR.md.
"""
__version__ = "0.3.0"
