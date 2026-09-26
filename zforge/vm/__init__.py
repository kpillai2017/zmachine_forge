"""The Z-machine version 5 interpreter.

    decoder.py   bytes -> Instruction (§4)            (pure; shared with disasm)
    frames.py    call frames, locals, evaluation stack (§5, §6)
    machine.py   the ZMachine: load, variables, fetch-decode-execute loop
    objects.py   the object table (§12)
    lexer.py     @read / @tokenise / dictionary lookup (§13)
    streams.py   output streams 1-4 (§7)
    quetzal.py   save files + undo snapshots (Quetzal standard)
    ops/         one module per opcode family (§15)
    screen/      the screen model (§8): plain, virtual (tests), curses
"""
