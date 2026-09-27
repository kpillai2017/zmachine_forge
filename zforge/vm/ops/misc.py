"""§15 miscellaneous opcodes: random, quit, restart, verify, nop,
save / restore (Quetzal) and save_undo / restore_undo."""
from __future__ import annotations

from pathlib import Path

from zforge.common.errors import QuitGame, RestartGame, ZMachineError
from zforge.common.header import compute_checksum
from zforge.common.numbers import to_signed
from zforge.vm import quetzal


def op_nop(vm):
    """§15 nop (0OP:180)."""


def op_quit(vm):
    """§15 quit (0OP:186): end the game."""
    raise QuitGame("quit")


def op_restart(vm):
    """§15 restart (0OP:183): reload the story (keeping Flags 2 bits 0-1)."""
    raise RestartGame()


def op_verify(vm):
    """§15 verify (0OP:189): branch if the checksum of the ORIGINAL file
    (bytes 0x40 .. file length) matches the header."""
    length = vm.header.file_length or len(vm.story)
    vm.branch(compute_checksum(vm.story, length) == vm.header.checksum)


def op_random(vm, range_):
    """§15 random (VAR:231):
       range > 0  -> a random number 1..range
       range < 0  -> seed the generator with |range| (predictable), return 0
       range == 0 -> re-seed randomly, return 0     (ADR-004)"""
    r = to_signed(range_)
    if r > 0:
        vm.store_result(vm.rng.randint(1, r))
    else:
        vm.rng.seed(-r if r < 0 else None)
        vm.store_result(0)


# ----------------------------------------------------------- save / restore
def _store_pc(vm) -> int:
    """The address of the current instruction's store byte (Quetzal, v5)."""
    return vm.current.next_address - 1


def _ask_filename(vm, verb: str) -> str:
    default = getattr(vm, "save_name", "story.qzl")
    vm.output(f"\n{verb} file name [{default}]: ")
    name = vm.screen.read_line(100).strip()
    return name or default


def op_save(vm, table=0, nbytes=0, name=0):
    """§15 save (EXT:0): store 1 on success, 0 on failure. With a table
    operand only those bytes are saved (auxiliary file); otherwise the whole
    game state is written as a Quetzal file."""
    filename = _ask_filename(vm, "Save")
    try:
        # Auxiliary file: save only the specified memory range
        if table:
            Path(filename).write_bytes(vm.mem.read_bytes(table, nbytes))
        # Full game state: encode as Quetzal (including stack, frames, all memory)
        else:
            Path(filename).write_bytes(quetzal.encode_save(vm, _store_pc(vm)))
        vm.store_result(1)
    except (OSError, ZMachineError) as exc:
        vm.output(f"[save failed: {exc}]\n")
        vm.store_result(0)


def op_restore(vm, table=0, nbytes=0, name=0):
    """§15 restore (EXT:1): on success execution continues after the SAVE
    that made the file, whose result becomes 2. On failure store 0."""
    filename = _ask_filename(vm, "Restore")
    try:
        data = Path(filename).read_bytes()
        # Auxiliary file: restore to the specified range
        if table:
            data = data[:nbytes]
            for i, b in enumerate(data):
                vm.mem.write_byte(table + i, b)
            vm.store_result(len(data))
            return
        # Full game state: decode Quetzal, get the resume point
        store_pc = quetzal.decode_save(vm, data)
    except (OSError, ZMachineError) as exc:
        vm.output(f"[restore failed: {exc}]\n")
        vm.store_result(0)
        return
    # Resume: write 2 to the store location of the original save, then jump there
    vm.write_variable(vm.mem.read_byte(store_pc), 2)
    vm.pc = store_pc + 1


def op_save_undo(vm):
    """§15 save_undo (EXT:9): snapshot the state in memory, store 1."""
    vm.undo_states.append(quetzal.snapshot(vm, _store_pc(vm)))
    del vm.undo_states[:-10]            # keep the last 10 undo levels
    vm.store_result(1)


def op_restore_undo(vm):
    """§15 restore_undo (EXT:10): return to the last save_undo, whose
    result becomes 2. Store 0 if there is nothing to undo."""
    if not vm.undo_states:
        vm.store_result(0)
        return
    # Pop the most recent snapshot and restore it
    state = vm.undo_states.pop()
    quetzal.restore_snapshot(vm, state)
    # Resume: write 2 to the store location of the save_undo, then jump there
    vm.write_variable(vm.mem.read_byte(state.store_pc), 2)
    vm.pc = state.store_pc + 1
