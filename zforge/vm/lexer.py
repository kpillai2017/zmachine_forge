"""§13 The dictionary and lexical analysis (@tokenise, the 2nd half of @read).

Dictionary layout (§13.2):
    byte   n                  number of word-separator characters
    n bytes                   the separators (ZSCII), e.g. '.' ',' '"'
    byte   entry length       at least 6 in v5 (4 bytes of text... + data)
    word   number of entries  (negative = unsorted, §13.2.3)
    entries                   each starts with the 6-byte encoded word

Tokenising splits the text buffer into words at spaces and separators;
each separator is also a word by itself (§13.5.1). For each word the parse
buffer gets a 4-byte block (§15 read):
    word  dictionary address of the word (0 if not found)
    byte  number of letters
    byte  position of the first letter in the TEXT BUFFER
"""
from __future__ import annotations

from dataclasses import dataclass

from zforge.common.memory import Memory
from zforge.common.numbers import to_signed
from zforge.common.text import Alphabets, encode_dictionary_word

ENCODED_WORD_BYTES = 6     # v4+: 9 z-chars


@dataclass
class Dictionary:
    address: int
    separators: list[int]
    entry_length: int
    count: int              # signed; negative means unsorted
    entries_start: int

    @classmethod
    def load(cls, mem: Memory, address: int) -> "Dictionary":
        n = mem.read_byte(address)
        separators = [mem.read_byte(address + 1 + i) for i in range(n)]
        entry_length = mem.read_byte(address + 1 + n)
        count = to_signed(mem.read_word(address + 2 + n))
        return cls(address, separators, entry_length, count, address + 4 + n)

    def lookup(self, mem: Memory, encoded: bytes) -> int:
        """Return the address of the entry for `encoded`, or 0.
        Sorted dictionaries allow binary search (§13.2.2); unsorted ones
        (negative count) need a linear scan."""
        count = abs(self.count)

        def key(i: int) -> bytes:
            return mem.read_bytes(self.entries_start + i * self.entry_length, ENCODED_WORD_BYTES)

        if self.count < 0:
            for i in range(count):
                if key(i) == encoded:
                    return self.entries_start + i * self.entry_length
            return 0
        lo, hi = 0, count - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            k = key(mid)
            if k == encoded:
                return self.entries_start + mid * self.entry_length
            if k < encoded:
                lo = mid + 1
            else:
                hi = mid - 1
        return 0


def split_words(chars: list[int], separators: list[int]) -> list[tuple[int, int]]:
    """Split ZSCII chars into words. Returns (start index, length) pairs."""
    words: list[tuple[int, int]] = []
    start = None
    for i, c in enumerate(chars):
        if c == 32 or c in separators:
            if start is not None:
                words.append((start, i - start))
                start = None
            if c in separators:
                words.append((i, 1))
        elif start is None:
            start = i
    if start is not None:
        words.append((start, len(chars) - start))
    return words


def tokenise(mem: Memory, alphabets: Alphabets, text_buffer: int, parse_buffer: int,
             dictionary: Dictionary, skip_unknown: bool = False) -> None:
    """§15 tokenise: fill parse_buffer from the v5 text buffer.

    v5 text buffer: byte 0 = max length, byte 1 = number of chars typed,
    chars from byte 2 (§15 read).
    """
    length = mem.read_byte(text_buffer + 1)
    chars = [mem.read_byte(text_buffer + 2 + i) for i in range(length)]
    max_words = mem.read_byte(parse_buffer)
    words = split_words(chars, dictionary.separators)[:max_words]
    mem.write_byte(parse_buffer + 1, len(words))
    for n, (start, size) in enumerate(words):
        encoded = encode_dictionary_word(chars[start:start + size], alphabets)
        entry = dictionary.lookup(mem, encoded)
        block = parse_buffer + 2 + 4 * n
        if entry == 0 and skip_unknown:
            continue                     # §15 tokenise: leave the slot untouched
        mem.write_word(block, entry)
        mem.write_byte(block + 2, size)
        mem.write_byte(block + 3, start + 2)   # position counts from buffer start
