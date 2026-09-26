"""The story-file linker: builds the tables and the header.

Memory layout we produce (§1.1):

    0x0000  header (64 bytes)                                   §11
            abbreviations table: 96 words -> one empty string   §3.3
            object table: 63 property defaults + 14-byte entries §12
            property tables (short name + properties)            §12.4
            global variables: 240 words                         §6.2
            arrays and buffers
    ------  static memory starts here (header 0x0E)
            dictionary                                          §13
    ------  high memory starts here (header 0x04), aligned (*)
            start stub:  call_vn main ; quit
            routines (each aligned (*), §1.2.3 packed addresses)
            strings  (each aligned (*))

(*) to VersionProfile.code_alignment: 4 bytes in v5, so 4P can reach it.

The file is padded to a multiple of 4 because v5 stores length / 4
(§11.1.6), and the checksum is computed last.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from zforge.common import header as H
from zforge.common.text import encode_dictionary_word, encode_string, text_to_zscii, UnicodeTable
from zforge.common.versions import VersionProfile

GLOBAL_COUNT = 240
ABBREVIATION_COUNT = 96
DICT_WORD_BYTES = 6


def align(address: int, boundary: int = 4) -> int:
    return (address + boundary - 1) // boundary * boundary


@dataclass
class ObjectDef:
    name: str
    short_name: str
    parent: str                       # a symbol or "0"
    attributes: list[int] = field(default_factory=list)
    # property number -> ("word"|"byte", [tokens])
    properties: dict[int, tuple[str, list[str]]] = field(default_factory=dict)
    line: int = 0


# --------------------------------------------------------------------- objects
def property_table_size(obj: ObjectDef) -> int:
    size = 1 + len(encode_string(obj.short_name))
    for kind, values in obj.properties.values():
        length = len(values) * (2 if kind == "word" else 1)
        size += (1 if length <= 2 else 2) + length
    return size + 1                      # the terminating 0 size byte


def encode_property_table(obj: ObjectDef, resolve) -> bytes:
    """§12.4: text-length byte, short name, properties high -> low, 0."""
    name = encode_string(obj.short_name)
    out = bytearray([len(name) // 2]) + name
    for number in sorted(obj.properties, reverse=True):
        kind, tokens = obj.properties[number]
        data = bytearray()
        for token in tokens:
            value = resolve(token)
            data += (value & 0xFFFF).to_bytes(2, "big") if kind == "word" else bytes([value & 0xFF])
        length = len(data)
        if length == 0 or length > 64:
            raise ValueError(f"property {number} of {obj.name} has length {length} (1..64)")
        if length <= 2:                  # one size byte: bit 6 = length 2
            out.append(number | (0x40 if length == 2 else 0))
        else:                            # two size bytes: 2nd has bit 7 set, 64 -> 0
            out += bytes([0x80 | number, 0x80 | (length % 64)])
        out += data
    out.append(0)
    return bytes(out)


def encode_object_entry(attributes: list[int], parent: int, sibling: int, child: int,
                        props_address: int) -> bytes:
    attr_bits = 0
    for a in attributes:
        attr_bits |= 1 << (47 - a)       # attribute 0 is the top bit (§12.3.1)
    return (attr_bits.to_bytes(6, "big") + parent.to_bytes(2, "big")
            + sibling.to_bytes(2, "big") + child.to_bytes(2, "big")
            + props_address.to_bytes(2, "big"))


# ------------------------------------------------------------------ dictionary
def dictionary_key(word: str) -> bytes:
    return encode_dictionary_word(text_to_zscii(word.lower(), UnicodeTable()))


def build_dictionary(words: list[str], separators: str,
                     address: int) -> tuple[bytes, dict[str, int]]:
    """§13.2: separators, entry length, count, then entries SORTED by their
    encoded bytes (so interpreters may binary-search)."""
    keyed: dict[bytes, str] = {}
    for w in words:
        keyed.setdefault(dictionary_key(w), w.lower())
    entries = sorted(keyed.items())
    seps = bytes(text_to_zscii(separators, UnicodeTable()))
    out = bytearray([len(seps)]) + seps + bytes([DICT_WORD_BYTES])
    out += len(entries).to_bytes(2, "big")
    addresses: dict[str, int] = {}
    for key, word in entries:
        addresses[word] = address + len(out)
        out += key
    # words that encode identically (truncated to 9 z-chars) share an entry
    for w in words:
        addresses.setdefault(w.lower(), addresses[keyed[dictionary_key(w)]])
    return bytes(out), addresses


# ---------------------------------------------------------------------- header
@dataclass
class HeaderFields:
    release: int
    serial: str
    high_memory: int
    initial_pc: int
    dictionary: int
    objects: int
    globals: int
    static_memory: int
    abbreviations: int
    flags2: int = 0


def write_header(story: bytearray, f: HeaderFields, profile: VersionProfile) -> None:
    def w(offset, value):
        story[offset:offset + 2] = (value & 0xFFFF).to_bytes(2, "big")
    story[H.H_VERSION] = profile.version
    w(H.H_RELEASE, f.release)
    w(H.H_HIGH_MEMORY, f.high_memory)
    w(H.H_INITIAL_PC, f.initial_pc)
    w(H.H_DICTIONARY, f.dictionary)
    w(H.H_OBJECTS, f.objects)
    w(H.H_GLOBALS, f.globals)
    w(H.H_STATIC_MEMORY, f.static_memory)
    w(H.H_FLAGS2, f.flags2)
    story[H.H_SERIAL:H.H_SERIAL + 6] = f.serial.encode("ascii")[:6].ljust(6, b"0")
    w(H.H_ABBREVIATIONS, f.abbreviations)


def finalise(story: bytearray, profile: VersionProfile) -> bytes:
    """Pad to a multiple of the file-length divisor (4 in v5), check the
    size limit (§1.1.4), then write the length (§11.1.6) and checksum."""
    divisor = profile.file_length_divisor
    while len(story) % divisor:
        story.append(0)
    if len(story) > profile.max_story_size:
        raise ValueError(f"story is {len(story)} bytes; v{profile.version} allows at most "
                         f"{profile.max_story_size // 1024}K")
    length = len(story)
    story[H.H_FILE_LENGTH:H.H_FILE_LENGTH + 2] = (length // divisor).to_bytes(2, "big")
    checksum = H.compute_checksum(story, length)
    story[H.H_CHECKSUM:H.H_CHECKSUM + 2] = checksum.to_bytes(2, "big")
    return bytes(story)
