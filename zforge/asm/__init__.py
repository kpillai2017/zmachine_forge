"""Assembler, story-file linker and disassembler.

    syntax.py     .zas text -> Directive / AsmInstruction records
    assembler.py  records -> sized instructions, branch relaxation
    linker.py     story-file layout (§1), header (§11), object table (§12),
                  dictionary (§13), packed addresses (§1.2.3), checksum
    disasm.py     story file -> readable listing (uses the VM's decoder)
    info.py       header / object tree / dictionary dump (like infodump)

The .zas language is documented in docs/ZAS_FORMAT.md.
"""
