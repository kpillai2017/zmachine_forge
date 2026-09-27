"""Saving and restoring: the Quetzal format (IFF "FORM" of type "IFZS"),
plus in-memory snapshots for @save_undo / @restore_undo.

Chunks we write (Quetzal standard 1.4):
    IFhd  13 bytes: release, serial (6), checksum, PC (3 bytes)
    CMem  dynamic memory XOR-ed with the original story, run-length
          encoded: a 0 byte is followed by a count of EXTRA zeros
    Stks  one record per frame (oldest first):
            PC (3 bytes)  flags  result-var  args-mask  eval-count (word)
            locals (words)  evaluation stack (words)
          flags bits 0-3 = number of locals, bit 4 = result is discarded

For v5 the saved PC is the address of the save instruction's STORE byte:
restoring reads that byte and stores 2 there ("restore succeeded").
"""
from __future__ import annotations

from dataclasses import dataclass

from zforge.common import header as H
from zforge.common.errors import ZMachineError
from zforge.vm.frames import Frame


def _chunk(kind: bytes, data: bytes) -> bytes:
    """Format a Quetzal chunk: kind (4 bytes) + size (4 bytes) + data + padding."""
    pad = b"\0" if len(data) % 2 else b""
    return kind + len(data).to_bytes(4, "big") + data + pad


def _compress(current: bytes, original: bytes) -> bytes:
    """Compress dynamic memory using XOR and run-length encoding (Quetzal CMem chunk).

    Each byte is XOR'd with the original; runs of zeros are RLE-encoded as (0, count-1).
    """
    out = bytearray()
    zeros = 0
    for a, b in zip(current, original, strict=True):   # same-size dynamic memory
        x = a ^ b
        if x == 0:
            zeros += 1
            continue
        # Flush any accumulated zeros
        while zeros:
            run = min(zeros, 256)
            out += bytes([0, run - 1])
            zeros -= run
        out.append(x)
    # trailing zeros may be omitted (the standard allows it)
    return bytes(out)


def _decompress(data: bytes, original: bytes) -> bytearray:
    """Decompress dynamic memory from Quetzal CMem chunk using XOR and RLE."""
    memory = bytearray(original)
    i = pos = 0
    while i < len(data):
        byte = data[i]
        i += 1
        # 0 byte signals a run of zeros: next byte is count-1
        if byte == 0:
            pos += data[i] + 1
            i += 1
        else:
            # XOR the byte back with the original
            memory[pos] ^= byte
            pos += 1
    return memory


def encode_save(vm, store_pc: int) -> bytes:
    """Encode the current VM state as a Quetzal save file.

    The Quetzal format (IFF FORM) contains:
    - IFhd: release, serial, checksum, PC (the store byte address in v5)
    - CMem: compressed dynamic memory (XOR + RLE)
    - Stks: all frames with locals and evaluation stacks
    """
    dynamic_size = vm.header.static_memory
    # Build the IFhd chunk: identify this save file
    ifhd = (vm.mem.read_word(H.H_RELEASE).to_bytes(2, "big")
            + vm.mem.read_bytes(H.H_SERIAL, 6)
            + vm.mem.read_word(H.H_CHECKSUM).to_bytes(2, "big")
            + store_pc.to_bytes(3, "big"))
    # Build the CMem chunk: compress only dynamic memory
    cmem = _compress(bytes(vm.mem.data[:dynamic_size]), vm.story[:dynamic_size])
    # Build the Stks chunk: all frames' locals and stacks
    stks = bytearray()
    for frame in vm.frames:
        # Flags: bits 0-3 = number of locals, bit 4 = result discarded
        flags = len(frame.locals) | (0x10 if frame.store_var is None else 0)
        # Arguments mask: one bit set for each argument supplied (up to 7)
        args_mask = (1 << min(frame.arg_count, 7)) - 1
        stks += frame.return_pc.to_bytes(3, "big")
        stks += bytes([flags, frame.store_var or 0, args_mask])
        stks += len(frame.stack).to_bytes(2, "big")
        # Locals, then stack values (all 2-byte words)
        for w in frame.locals + frame.stack:
            stks += w.to_bytes(2, "big")
    # Assemble the FORM with all chunks
    body = b"IFZS" + _chunk(b"IFhd", ifhd) + _chunk(b"CMem", cmem) + _chunk(b"Stks", bytes(stks))
    return b"FORM" + len(body).to_bytes(4, "big") + body


def _chunks(data: bytes):
    if data[:4] != b"FORM" or data[8:12] != b"IFZS":
        raise ZMachineError("Not a Quetzal save file")
    i = 12
    while i + 8 <= len(data):
        kind, size = data[i:i + 4], int.from_bytes(data[i + 4:i + 8], "big")
        yield kind, data[i + 8:i + 8 + size]
        i += 8 + size + (size % 2)


def decode_save(vm, data: bytes) -> int:
    """Restore memory + frames into vm. Returns the saved store-byte PC."""
    chunks = dict(_chunks(data))
    ifhd = chunks.get(b"IFhd")
    if not ifhd:
        raise ZMachineError("Save file has no IFhd chunk")
    # Verify the save file is from the same story
    expected = (vm.mem.read_word(H.H_RELEASE).to_bytes(2, "big")
                + vm.mem.read_bytes(H.H_SERIAL, 6)
                + vm.mem.read_word(H.H_CHECKSUM).to_bytes(2, "big"))
    if ifhd[:10] != expected:
        raise ZMachineError("Save file is from a different story (release/serial/checksum)")
    # Decompress or extract dynamic memory
    dynamic_size = vm.header.static_memory
    if b"CMem" in chunks:
        memory = _decompress(chunks[b"CMem"], vm.story[:dynamic_size])
    elif b"UMem" in chunks:
        memory = bytearray(chunks[b"UMem"])
    else:
        raise ZMachineError("Save file has no memory chunk")
    # Reconstruct frames from the Stks chunk
    frames = []
    stks, i = chunks[b"Stks"], 0
    while i < len(stks):
        return_pc = int.from_bytes(stks[i:i + 3], "big")
        flags, var, args_mask = stks[i + 3], stks[i + 4], stks[i + 5]
        n_stack = int.from_bytes(stks[i + 6:i + 8], "big")
        n_locals = flags & 0x0F
        i += 8
        # Read locals and stack values (all 2-byte words)
        words = [int.from_bytes(stks[i + 2 * k:i + 2 * k + 2], "big")
                 for k in range(n_locals + n_stack)]
        i += 2 * (n_locals + n_stack)
        # Reconstruct the frame
        frames.append(Frame(return_pc, words[:n_locals],
                            None if flags & 0x10 else var,
                            bin(args_mask).count("1"), words[n_locals:]))
    # Keep the interpreter-owned header fields (§11) and Flags 2 bits 0-1
    flags2 = vm.mem.read_word(H.H_FLAGS2)
    vm.mem.data[:dynamic_size] = memory[:dynamic_size]
    vm.frames = frames or vm.frames
    vm.set_interpreter_header()
    # Preserve Flags 2 bits 0-1 (transcript and fixed-pitch)
    new_flags2 = (vm.mem.read_word(H.H_FLAGS2) & ~0b11) | (flags2 & 0b11)
    vm.mem.write_header_word(H.H_FLAGS2, new_flags2)
    # Return the store PC so the caller can store the result (2 for success)
    return int.from_bytes(ifhd[10:13], "big")


@dataclass
class UndoState:
    """In-memory snapshot for @restore_undo (faster than Quetzal files)."""
    memory: bytes
    frames: list[Frame]
    store_pc: int


def snapshot(vm, store_pc: int) -> UndoState:
    """Create an in-memory snapshot of the current VM state for undo."""
    return UndoState(bytes(vm.mem.data[:vm.header.static_memory]),
                     [f.copy() for f in vm.frames], store_pc)


def restore_snapshot(vm, state: UndoState) -> None:
    """Restore the VM to a previously saved snapshot state."""
    vm.mem.data[:len(state.memory)] = state.memory
    vm.frames = [f.copy() for f in state.frames]
    vm.set_interpreter_header()
