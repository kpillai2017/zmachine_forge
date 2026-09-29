"""Blorb: the wrapper most modern interactive fiction is released in.

A Blorb file (`.zblorb`, `.blb`) packs a game with its cover art, pictures and
sounds. zforge only needs the game. The format (Blorb 2.0, Andrew Plotkin) is
IFF: the file is one `FORM` chunk of type `IFRS`, holding chunks of

    4-byte type   4-byte length (big-endian)   data   (one pad byte if odd)

The first chunk is the resource index, `RIdx`: a count, then 12-byte entries
of usage ("Exec", "Pict", "Snd "...), resource number and the file offset of
the resource's chunk. The game is resource Exec 0; its chunk type says what
kind of game it is - `ZCOD` for the Z-machine, `GLUL` for Glulx.

`story_bytes` hands back the Z-code inside a Blorb, and any other file as it
is, so the rest of zforge never has to know Blorbs exist (ADR-061).
"""

import struct

from zforge.common.errors import ZForgeError


def _chunks(data: bytes):
    """(type, start of the chunk, its data) for each chunk inside the FORM."""
    pos = 12
    while pos + 8 <= len(data):
        kind = data[pos:pos + 4]
        (size,) = struct.unpack(">I", data[pos + 4:pos + 8])
        yield kind, pos, data[pos + 8:pos + 8 + size]
        pos += 8 + size + (size & 1)


def _exec_chunk(data: bytes, name: str):
    """The game's chunk: from the resource index, else the first game chunk."""
    for kind, _, body in _chunks(data):
        if kind == b"RIdx":
            (count,) = struct.unpack(">I", body[:4])
            for i in range(count):
                usage, number, start = struct.unpack(">4sII", body[4 + 12 * i:16 + 12 * i])
                if usage == b"Exec" and number == 0:
                    (size,) = struct.unpack(">I", data[start + 4:start + 8])
                    return data[start:start + 4], data[start + 8:start + 8 + size]
            raise ZForgeError(f"{name}: this Blorb holds no game (no Exec resource)")
    for kind, _, body in _chunks(data):     # no index: take the first game chunk
        if kind in (b"ZCOD", b"GLUL"):
            return kind, body
    raise ZForgeError(f"{name}: this Blorb holds no game")


def story_bytes(data: bytes, name: str = "story") -> bytes:
    """The Z-machine story in DATA: unwrapped from a Blorb, or DATA itself."""
    if data[:4] != b"FORM":
        return data                               # a plain .z5 / .z8 file
    form = data[8:12]
    if form == b"IFZS":
        raise ZForgeError(f"{name}: this is a saved game, not a story - "
                          "load it with RESTORE while playing")
    if form != b"IFRS":
        raise ZForgeError(f"{name}: an IFF file of type {form.decode('latin-1')!r}, "
                          "not a story or a Blorb")
    kind, body = _exec_chunk(data, name)
    if kind == b"GLUL":
        raise ZForgeError(f"{name}: this Blorb holds a Glulx game; "
                          "zforge runs Z-machine games only (try a Glulx interpreter)")
    if kind != b"ZCOD":
        raise ZForgeError(f"{name}: this Blorb holds a {kind.decode('latin-1')!r} game, "
                          "not a Z-machine one")
    return body
