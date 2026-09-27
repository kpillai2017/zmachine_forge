"""`zforge info`: header, object tree and dictionary dump (like infodump)."""
from __future__ import annotations

from zforge.common import header as H
from zforge.common.text import Alphabets, UnicodeTable, decode_zchars, unpack_zchars
from zforge.vm.lexer import Dictionary
from zforge.vm.objects import ObjectTable
from zforge.common.memory import Memory


def _mem(story: bytes) -> tuple[H.Header, Memory]:
    """Parse header and return the header and memory object for a story file."""
    h = H.Header.parse(story)
    return h, Memory(story, h.static_memory, h.high_memory)


def header_report(story: bytes) -> str:
    """Return a formatted report of the story file header fields (§11)."""
    h, _ = _mem(story)
    ok = H.compute_checksum(story, h.file_length or len(story)) == h.checksum
    rows = [("Version", h.version), ("Release", h.release), ("Serial", h.serial),
            ("High memory", f"0x{h.high_memory:04x}"),
            # §5.4: v6 starts by calling a routine; the others start at a byte address (§5.5)
            (("Main routine", f"0x{h.main_routine:04x} (packed {h.initial_pc})")
             if h.profile.starts_with_main_routine else ("Initial PC", f"0x{h.initial_pc:04x}")),
            ("Dictionary", f"0x{h.dictionary:04x}"), ("Object table", f"0x{h.objects:04x}"),
            ("Globals", f"0x{h.globals:04x}"), ("Static memory", f"0x{h.static_memory:04x}"),
            ("Abbreviations", f"0x{h.abbreviations:04x}"),
            ("File length", f"{h.file_length} bytes"),
            ("Checksum", f"0x{h.checksum:04x} ({'ok' if ok else 'MISMATCH'})")]
    if h.profile.uses_packing_offsets:                # §1.2.3: v6/v7 only
        for label, offset in (("Routines offset", h.routines_offset),
                              ("Strings offset", h.strings_offset)):
            rows.append((label, f"0x{offset:04x} (x8 = 0x{8 * offset:05x})"))
    return "\n".join(f"  {k:<15} {v}" for k, v in rows)


def count_objects(mem: Memory, h: H.Header) -> int:
    """No count is stored: objects run until the first property table
    (property tables follow the entries in every normal story file)."""
    table = ObjectTable(mem, h.objects)
    n, lowest_props = 0, 0x10000
    while True:
        entry = table.first_entry + n * 14
        if entry >= lowest_props or entry + 14 > len(mem):
            return n
        n += 1
        lowest_props = min(lowest_props, table.property_table(n))


def object_report(story: bytes) -> str:
    """Return a formatted report of the object tree (§12.3), with attributes
    and properties for each object."""
    h, mem = _mem(story)
    table = ObjectTable(mem, h.objects)
    a, u = Alphabets.default(), UnicodeTable()

    def name(o: int) -> str:
        """Decode an object's short name."""
        zchars, _ = unpack_zchars(mem.read_word, table.short_name_address(o))
        return decode_zchars(zchars, a, u, None)

    lines, n = [], count_objects(mem, h)

    def describe(o: int, depth: int) -> None:
        """Recursively describe an object and its children."""
        attrs = [i for i in range(48) if table.test_attr(o, i)]
        props = [p for p, _length, _data in table.properties(o)]
        lines.append(f"{'  ' * depth}[{o}] \"{name(o)}\"  attrs={attrs}  props={props}")
        child = table.child(o)
        while child:                      # children, then their siblings
            describe(child, depth + 1)
            child = table.sibling(child)

    for o in range(1, n + 1):
        if table.parent(o) == 0:          # roots of the object tree
            describe(o, 0)
    return f"  {n} objects\n" + "\n".join("  " + line for line in lines)


def dictionary_report(story: bytes) -> str:
    """Return a formatted report of the dictionary (§13): separators and all
    words in the story file."""
    h, mem = _mem(story)
    d = Dictionary.load(mem, h.dictionary)
    a, u = Alphabets.default(), UnicodeTable()
    # Decode each dictionary entry (§13.4: 6-byte encoded form = 9 Z-characters).
    words = []
    for i in range(abs(d.count)):
        address = d.entries_start + i * d.entry_length
        zchars, _ = unpack_zchars(mem.read_word, address)
        words.append(decode_zchars(zchars, a, u, None))
    seps = "".join(chr(c) for c in d.separators)
    return f"  separators: {seps!r}  entries: {len(words)}\n  " + " ".join(words)
